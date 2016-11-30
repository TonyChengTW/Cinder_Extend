# Copyright (C) 2012 - 2014 EMC Corporation.
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

"""The clonechain api."""

from oslo_log import log as logging
import webob
from cinder.api import extensions
from cinder.api.openstack import wsgi
from cinder.fh.volume import api
from cinder import exception
from cinder import objects
from cinder.volume import utils as volume_utils

LOG = logging.getLogger(__name__)


class SnapshotClonechainController(wsgi.Controller):
    """The cgsnapshots API controller for the OpenStack API."""

    def __init__(self):
        self.volume_api = api.FhAPI()
        super(SnapshotClonechainController, self).__init__()
        LOG.debug("wsgi_actions :%s" % self.wsgi_actions)

    def show(self, req, id):
        """Return data about the given cgsnapshot."""
        LOG.debug('show called for member %s', id)
        context = req.environ['cinder.context']

        try:
            snapshot_obj = objects.Snapshot.get_by_id(context, id)
            db_volume = self.volume_api.get(context, snapshot_obj.volume_id)
        except exception.SnapshotNotFound as error:
            raise webob.exc.HTTPNotFound(explanation=error.msg)
        host = volume_utils.extract_host(db_volume['host'])
        return self.volume_api.get_snapshot_clone_chain(context,
                                                        snapshot_obj,
                                                        host)


class Snapshot_clonechain(extensions.ExtensionDescriptor):
    """cgsnapshots support."""

    name = 'snapshot_clonechain'
    alias = 'snapshot_clonechain'
    namespace = 'http://docs.openstack.org/volume/ext/snapshot_clone_chain/api/v1'
    updated = '2014-08-18T00:00:00+00:00'

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(
            Snapshot_clonechain.alias, SnapshotClonechainController())
        resources.append(res)
        return resources
