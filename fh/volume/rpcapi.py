# Copyright 2012, Intel, Inc.
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

"""
Client side of the volume RPC API.
"""

from cinder.volume.rpcapi import *


class FhVolumeAPI(VolumeAPI):
    def __init__(self):
        super(FhVolumeAPI, self).__init__()

    def get_volume_snapshots(self, ctxt, volume):
        host = utils.extract_host(volume['host'])
        new_host = utils.extract_host(host)
        cctxt = self.client.prepare(server=new_host, version='1.23')
        return cctxt.call(ctxt, 'get_volume_snapshots', volume=volume)

    def get_snapshot_children(self, ctxt, snapshot, volume):
        new_host = utils.extract_host(volume['host'])
        cctxt = self.client.prepare(server=new_host, version='1.23')
        return cctxt.call(ctxt, 'get_snapshot_children',
                          snapshot=snapshot)

    def get_volume_clone_chain(self, ctxt, volume):
        host = utils.extract_host(volume['host'])
        new_host = utils.extract_host(host)
        cctxt = self.client.prepare(server=new_host, version='1.23')
        return cctxt.call(ctxt, 'get_volume_clone_chain', volume=volume)

    def get_snapshot_clone_chain(self, ctxt, snapshot, host):
        cctxt = self.client.prepare(server=host, version='1.23')
        return cctxt.call(ctxt, 'get_snapshot_clone_chain', snapshot=snapshot)
