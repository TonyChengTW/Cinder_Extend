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

"""Handles all requests relating to volumes."""
from cinder.volume.api import *
from cinder.fh.volume import rpcapi as volume_rpcapi


class FhAPI(API):
    def __init__(self, db_driver=None, image_service=None):
        super(FhAPI, self).__init__(db_driver, image_service)
        self.volume_rpcapi = volume_rpcapi.FhVolumeAPI()

    def get_volume_snapshots(self, context, volume):
        return self.volume_rpcapi.get_volume_snapshots(context, volume)

    def get_snapshot_children(self, context, snapshot):
        volume = self.db.volume_get(context, snapshot.volume_id)
        return self.volume_rpcapi.get_snapshot_children(context, snapshot,
                                                        volume)

    def get_volume_clone_chain(self, context, volume):
        return self.volume_rpcapi.get_volume_clone_chain(context, volume)

    def get_snapshot_clone_chain(self, context, snapshot, host):
        return self.volume_rpcapi.get_snapshot_clone_chain(context,
                                                           snapshot, host)
