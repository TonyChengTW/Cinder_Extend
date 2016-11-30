#    Copyright 2013 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""FiberHome RADOS Block Device Driver"""

from cinder.i18n import _LI
from oslo_utils import encodeutils
from oslo_utils import uuidutils
from oslo_log import log as logging

from .rbd import RBDDriver
from .rbd import RBDVolumeProxy

LOG = logging.getLogger(__name__)


class RBDDriver(RBDDriver):
    def __init__(self, *args, **kwargs):
        super(RBDDriver, self).__init__(*args, **kwargs)

    # ----------------------------- added by zhangjun --------------------------
    def get_volume_snapshots(self, volume):
        """
        get all snapshots created on the volume.
        """
        LOG.debug('get_volume_snapshot starts')
        pool_name = self.configuration.rbd_pool
        volume_name = 'volume-%s' % encodeutils.safe_encode(volume["id"])
        snaps_on_vol = self._get_volume_snapshots(pool_name, volume_name)
        snapshots = list()
        if snaps_on_vol is not None:
            for snap in snaps_on_vol:
                snap_name = str(snap["name"])
                item = dict()
                if snap_name.startswith("snapshot-"):
                    # snapshot directly created on volume.
                    item["type"] = "volume_snap"
                    item["uuid"] = snap_name[len('snapshot-'):]
                elif snap_name.startswith("volume-") and \
                        snap_name.endswith(".clone_snap"):
                    # snapshot used for create volume on volume.
                    item["type"] = "clone_snap"
                    item["uuid"] = snap_name[len("volume-"):-len(".clone_snap")]
                elif snap_name.startswith("backup.") and ".snap." in snap_name:
                    # snapshot used for backup volume.
                    item["type"] = "backup_snap"
                    item["uuid"] = \
                        snap_name[len("backup."):snap_name.index(".snap.")]
                else:
                    item["type"] = ""
                    item["uuid"] = ""
                snapshots.append(item)

        LOG.debug('volume snapshots: %s', snapshots)
        LOG.debug('get_volume_snapshots finished.')
        return snapshots

    def get_snapshot_children(self, snapshot):
        """
        get all cloned volumes created on the snapshot.
        """
        LOG.debug('get_snapshot_children starts.')
        pool_name = self.configuration.rbd_pool
        volume_name = \
            'volume-%s' % encodeutils.safe_encode(snapshot["volume_id"])
        snap_name = 'snapshot-%s' % encodeutils.safe_encode(snapshot['id'])
        children = list()
        children_on_snap = \
            self._get_snapshot_children(pool_name, volume_name, snap_name)
        if children_on_snap is not None:
            for child in children_on_snap:
                item = dict()
                if len(child) == 2:
                    item["pool_name"] = child[0]
                    item["volume_name"] = child[1]
                    if child[1].startswith("volume-"):
                        item["type"] = "volume"
                        item["uuid"] = child[1][len("volume-"):]
                    elif uuidutils.is_uuid_like(child[1]):
                        item["type"] = "volume"
                        item["uuid"] = child[1]
                    else:
                        item["type"] = ""
                        item["uuid"] = ""
                    children.append(item)

        LOG.debug('snapshot children: %s', children)
        LOG.debug('get_snapshot_children finished.')
        return children

    def _generate_chain_obj(self, pool_name, volume_name, snap_name=None):
        obj = dict()
        obj["location"] = dict()
        obj["location"]["pool_name"] = pool_name
        obj["location"]["volume_name"] = volume_name
        obj["children"] = list()
        if snap_name is None:
            obj["type"] = "volume"
            if volume_name.startswith("volume-"):
                obj["usage"] = "volume"
            elif volume_name.endswith("_disk"):
                obj["usage"] = "vm"
            elif uuidutils.is_uuid_like(volume_name):
                obj["usage"] = "volume"
            else:
                obj["usage"] = ""
        else:
            obj["type"] = "snapshot"
            obj["location"]["snap_name"] = snap_name
            if snap_name.startswith("snapshot-"):
                obj["usage"] = "volume_snap"
            elif snap_name.startswith("volume-") and \
                    snap_name.endswith(".clone_snap"):
                obj["usage"] = "clone_snap"
            elif snap_name.startswith("backup.") and ".snap." in snap_name:
                obj["usage"] = "backup_snap"
            elif snap_name == "snap":
                obj["usage"] = "image_snap"
            else:
                obj["usage"] = ""

        return obj

    def _get_volume_snapshots(self, pool_name, volume_name):
        try:
            with RBDVolumeProxy(self, volume_name, pool=pool_name) as volume:
                return volume.list_snaps()
        except self.rbd.ImageNotFound:
            LOG.info(_LI("volume %s no longer exists in backend"), volume_name)
            return None
        except self.rados.ObjectNotFound:
            LOG.info(_LI("error connecting to ceph pool %s"), pool_name)
            return None

    def _get_snapshot_children(self, pool_name, volume_name, snap_name):
        try:
            with RBDVolumeProxy(self, volume_name, pool=pool_name) as volume:
                try:
                    volume.set_snap(snap_name)
                    return volume.list_children()
                except self.rbd.ImageNotFound:
                    LOG.info(_LI("snapshot %s no longer exists in backend"),
                             snap_name)
                    return None
                finally:
                    volume.set_snap(None)
        except self.rbd.ImageNotFound:
            LOG.info(_LI("volume %s no longer exists in backend"), volume_name)
            return None
        except self.rados.ObjectNotFound:
            LOG.info(_LI("error connecting to ceph pool %s"), pool_name)
            return None

    def _get_parent_info(self, pool_name, volume_name):
        try:
            with RBDVolumeProxy(self, volume_name, pool=pool_name) as volume:
                try:
                    return volume.parent_info()
                except self.rbd.ImageNotFound:
                    LOG.info(_LI("volume %s doesn't have a parent"),
                             volume_name)
                    return None
        except self.rbd.ImageNotFound:
            LOG.info(_LI("volume %s no longer exists in backend"), volume_name)
            return None
        except self.rados.ObjectNotFound:
            LOG.info(_LI("error connecting to ceph pool %s"), pool_name)
            return None

    def _get_parent_chain(self, parent_chain, chain, pool_name, volume_name,
                          snap_name=None):
        if snap_name is not None:
            obj = self._generate_chain_obj(pool_name, volume_name, None)
            obj["children"].append(chain)
            self._get_parent_chain(parent_chain, obj, pool_name,
                                   volume_name, None)
        else:
            parent = self._get_parent_info(pool_name, volume_name)
            if parent is not None and len(parent) == 3:
                obj = self._generate_chain_obj(parent[0], parent[1], parent[2])
                obj["children"].append(chain)
                self._get_parent_chain(parent_chain, obj, parent[0], parent[1],
                                       parent[2])
            else:
                for key in chain.keys():
                    parent_chain[key] = chain[key]

    def _get_children_chain(self, chain, pool_name, volume_name,
                            snap_name=None):
        if snap_name is None:
            snaps_on_volume = self._get_volume_snapshots(pool_name, volume_name)
            if snaps_on_volume is not None:
                for snap in snaps_on_volume:
                    obj = self._generate_chain_obj(pool_name,
                                                   volume_name, snap["name"])
                    chain.append(obj)
                    self._get_children_chain(obj["children"], pool_name,
                                             volume_name, snap["name"])
        else:
            volume_on_snap = \
                self._get_snapshot_children(pool_name, volume_name, snap_name)
            if volume_on_snap is not None:
                for volume in volume_on_snap:
                    obj = self._generate_chain_obj(volume[0], volume[1], None)
                    chain.append(obj)
                    self._get_children_chain(obj["children"], volume[0],
                                             volume[1], None)

    def _get_full_clone_chain(self, pool_name, volume_name, snap_name=None):
        """
        get full clone chain of a volume or snapshot.
        """
        full_clone_chain = dict()
        # get children clone chain.
        obj = self._generate_chain_obj(pool_name, volume_name, snap_name)
        self._get_children_chain(obj["children"], pool_name, volume_name,
                                 snap_name)
        # get parent clone chain.
        self._get_parent_chain(full_clone_chain, obj, pool_name, volume_name,
                               snap_name)
        return full_clone_chain

    def get_volume_clone_chain(self, volume):
        """
        get volume's clone chain.
        """
        LOG.debug('get_volume_clone_chain starts.')
        volume_name = 'volume-%s' % encodeutils.safe_encode(volume["id"])
        pool_name = self.configuration.rbd_pool
        clone_chain = self._get_full_clone_chain(pool_name, volume_name, None)
        LOG.debug('volume clone chain: %s', clone_chain)
        LOG.debug('get_volume_clone_chain finished.')
        return clone_chain

    def get_snapshot_clone_chain(self, snapshot):
        """
        get snapshot's clone chain
        """
        LOG.debug('get_snapshot_clone_chain starts.')
        volume_name = 'volume-%s' % \
                      encodeutils.safe_encode(snapshot["volume_id"])
        snap_name = 'snapshot-%s' % encodeutils.safe_encode(snapshot['id'])
        pool_name = self.configuration.rbd_pool
        clone_chain = self._get_full_clone_chain(pool_name, volume_name,
                                                 snap_name)
        LOG.debug('snapshot clone chain: %s', clone_chain)
        LOG.debug('get_snapshot_clone_chain finished.')
        return clone_chain
    # ----------------------------- added by zhangjun --------------------------
