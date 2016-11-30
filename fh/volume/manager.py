# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

import oslo_messaging as messaging
from oslo_log import log as logging
from cinder.volume import manager as volume_manager

LOG = logging.getLogger(__name__)


class FhVolumeManager(volume_manager.VolumeManager):
    """The volume manager of fenghuo."""

    RPC_API_VERSION = '1.30'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, volume_driver=None, service_name=None, *args, **kwargs):
        """Load the driver from the one specified in args, or from flags."""
        # update_service_capabilities needs service_name to be volume
        super(FhVolumeManager, self).__init__(volume_driver=volume_driver,
                                              service_name=service_name,
                                              *args, **kwargs)

    def get_volume_snapshots(self, ctxt, volume):
        LOG.debug('retrieving snapshots of given volume: %(volume_id)s',
                  {'volume_id': volume['id']})
        return self.driver.get_volume_snapshots(volume)

    def get_snapshot_children(self, ctxt, snapshot):
        LOG.debug('retrieving snapshot children: %(snapshot_id)s',
                  {'snapshot_id': snapshot['id']})
        return self.driver.get_snapshot_children(snapshot)

    def get_volume_clone_chain(self, ctxt, volume):
        LOG.debug('retrieving snapshots of given volume: %(volume_id)s',
                  {'volume_id': volume['id']})
        return self.driver.get_volume_clone_chain(volume)

    def get_snapshot_clone_chain(self, ctxt, snapshot):
        LOG.debug('retrieving snapshots of given snapshot: %(snapshot_id)s',
                  {'volume_id': snapshot['id']})
        return self.driver.get_snapshot_clone_chain(snapshot)
