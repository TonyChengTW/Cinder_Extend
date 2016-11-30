#   Copyright 2012 OpenStack Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

"""The Extended Snapshot Tree API extension."""

from oslo_log import log as logging

from cinder.api import extensions
from cinder.api.openstack import wsgi
from cinder.api import xmlutil

from cinder.fh.volume import api

LOG = logging.getLogger(__name__)
authorize = extensions.soft_extension_authorizer(
    'volume',
    'extended_snapshot_trees')


class ExtendedSnapshotTreesController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(ExtendedSnapshotTreesController, self).__init__(*args, **kwargs)
        self.volume_api = api.FhAPI()

    def _extend_snapshot(self, req, context, resp_snap):
        db_snap = req.get_db_snapshot(resp_snap['id'])
        snap_children = self.volume_api.get_snapshot_children(context, db_snap)
        resp_snap['%s:tree' % Extended_snapshot_trees.alias] = \
            {"child": snap_children}

    @wsgi.extends
    def show(self, req, resp_obj, id):
        context = req.environ['cinder.context']
        if authorize(context):
            # Attach our slave template to the response object
            resp_obj.attach(xml=ExtendedSnapshotAttributeTemplate())
            snapshot = resp_obj.obj['snapshot']
            self._extend_snapshot(req, context, snapshot)

    # @wsgi.extends
    # def detail(self, req, resp_obj):
    #     context = req.environ['cinder.context']
    #     if authorize(context):
    #         # Attach our slave template to the response object
    #         resp_obj.attach(xml=ExtendedSnapshotAttributesTemplate())
    #         for snapshot in list(resp_obj.obj['snapshots']):
    #             self._extend_snapshot(req, context, snapshot)


class Extended_snapshot_trees(extensions.ExtensionDescriptor):
    """Extended SnapshotAttributes support."""

    name = "ExtendedSnapshotTrees"
    alias = "os-extended-snapshot-trees"
    namespace = ("http://docs.openstack.org/snapshot/ext/"
                 "extended_snapshot_trees/api/v1")
    updated = "2016-01-27T00:00:00+00:00"

    def get_controller_extensions(self):
        controller = ExtendedSnapshotTreesController()
        extension = extensions.ControllerExtension(self, 'snapshots',
                                                   controller)
        return [extension]


def make_snapshot(elem):
    elem.set('{%s}tree' % Extended_snapshot_trees.namespace,
             '%s:tree' % Extended_snapshot_trees.alias)


class ExtendedSnapshotAttributeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('snapshot', selector='snapshot')
        make_snapshot(root)
        alias = Extended_snapshot_trees.alias
        namespace = Extended_snapshot_trees.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})


class ExtendedSnapshotAttributesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('snapshots')
        elem = xmlutil.SubTemplateElement(root, 'snapshot',
                                          selector='snapshots')
        make_snapshot(elem)
        alias = Extended_snapshot_trees.alias
        namespace = Extended_snapshot_trees.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})
