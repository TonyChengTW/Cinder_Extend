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

LOG = logging.getLogger(__name__)


class VolumeClonechainController(wsgi.Controller):
    """The cgsnapshots API controller for the OpenStack API."""

    def __init__(self):
        self.volume_api = api.FhAPI()
        super(VolumeClonechainController, self).__init__()
        LOG.debug("wsgi_actions :%s" % self.wsgi_actions)

    def show(self, req, id):
        """Return data about the given cgsnapshot."""
        LOG.debug('show called for member %s', id)
        context = req.environ['cinder.context']
        try:
            db_volume = self.volume_api.get(context, id)
        except exception.VolumeNotFound as error:
            raise webob.exc.HTTPNotFound(explanation=error.msg)
        return self.volume_api.get_volume_clone_chain(context, db_volume)


class Volume_clonechain(extensions.ExtensionDescriptor):
    """cgsnapshots support."""

    name = 'volume_clonechain'
    alias = 'volume_clonechain'
    namespace = 'http://docs.openstack.org/volume/ext/volume_clone_chain/api/v1'
    updated = '2014-08-18T00:00:00+00:00'

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(
            Volume_clonechain.alias, VolumeClonechainController())
        resources.append(res)
        return resources
