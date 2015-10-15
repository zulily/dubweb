#!/usr/bin/env python
"""
rackspace helper library
   Called by flask app
   to handle rackspace-specific functions, etc.

   Copyright 2015 zulily, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from app import app
import app.utils as utils

import requests
import pyfscache
from collections import defaultdict
import simplejson as json

#globals
SETTINGS_FILE = "/var/dubweb/.raxcloud_settings"
RACK_AUTH_URL = "https://identity.api.rackspacecloud.com/v2.0/tokens"
RACK_SRV_URL = "https://%s.servers.api.rackspacecloud.com/v2/%s/servers/detail?limit=300"
DEFAULT_HOST_WEIGHT = 10
CACHE_HOURS = 24

# settings
requests.packages.urllib3.disable_warnings()

def format_hostmap(host, count, vms_string):
    """
    Helper for hostmap formatting
    """
    data_point = {}
    data_point["Host"] = host
    data_point["Load"] = count
    data_point["VMs"] = vms_string
    return data_point


def weight(prefix):
    """
    Return vm weight (default to 2)
    """
    return {
        'foo'    : 8,
        'foobar'    : 8,
        'bar' : 3,
    }.get(prefix, 2)

def _calculate_vm_load(vm_list):
    """
    Given a list of VMs,
    Calculate the sum of the load.
    """
    load = 0
    for server in vm_list:
        pos = server.rfind('-')
        if pos < 0:
            pos = len(server)-1
        load += weight(server[:pos])
    return load

def _get_rackspace_auth(acct_data):
    """
    Given a rackspace cloud account/apikey,
    Retrieve a valid auth token for API calls.
    """
    payload = {"auth":{"RAX-KSKEY:apiKeyCredentials":
                       {"username":acct_data[0], "apiKey":acct_data[2]}}}
    header = {"Content-type" : "application/json"}
    req = requests.post(RACK_AUTH_URL, json=payload, headers=header)
    response = req.json()
    return response['access']['token']['id']


def _get_rackspace_serverdetails(account, auth, dc_id, id_dict, name_dict):
    """
    Given a rackspace cloud account and auth token,
    Retrieve lists of vms by id and name.
    """
    serverlist = []
    serverdetails = None
    url = RACK_SRV_URL % (dc_id, account[1])
    header = {"X-Auth-Token" : auth, "Content-type" : "application/json"}
    reqs = requests.get(url, headers=header)
    output = reqs.content
    try:
        if output:
            serverdetails = json.loads(output)
    except AttributeError:
        app.logger.debug("server json not loaded for %s", account[0])
        serverdetails = None
    if serverdetails:
        serverlist = serverdetails['servers']
        for server in serverlist:
            id_dict[server['hostId']].append(server['id'])
            name_dict[server['hostId']].append(server['name'])
    return id_dict, name_dict

def retrieve_cloud_hostmap(dc_id, account_filter, allow_cache):
    """
    Given a datacenter prefix, and optional
    cloud account (for filtering)
    Return a dictionary of cloud hypervisors,
    with a list of our servers on each.
    """
    id_map = defaultdict(list)
    name_map = defaultdict(list)
    cache_it = pyfscache.FSCache('/tmp/', hours=CACHE_HOURS)

    if not account_filter and allow_cache:
        if (dc_id, ['key']) in cache_it:
            return None, cache_it[(dc_id, ['key'])]
    account_list = utils.load_json_definition_file(SETTINGS_FILE)

    if dc_id in account_list:
        accounts = account_list[dc_id]
        if account_filter:
            accounts[:] = (a for a in accounts if a[0] == account_filter)
    else:
        app.logger.error("invalid datacenter: %s", dc_id)

    for acct in accounts:
        authstring = _get_rackspace_auth(acct)
        id_map, name_map = _get_rackspace_serverdetails(acct, authstring, dc_id,
                                                        id_map, name_map)
    if not account_filter:
        try:
            cache_it.expire((dc_id, ['key']))
        except pyfscache.CacheError:
            #No cache = No worries
            app.logger.debug("Cache not found for %s", dc_id)

        cache_it[(dc_id, ['key'])] = name_map

    return id_map, name_map


def check_host_capacity(dc_id, vmid, max_weight):
    """
    Given a datacenter prefix, a VM id and an
    optional weighting strategy,
    check whether the VM is on an overloaded host,
    Return OK, OVERLOADED, ERROR
    """
    retval = "ERROR"

    if not max_weight:
        max_weight = DEFAULT_HOST_WEIGHT
    id_map, name_map = retrieve_cloud_hostmap(dc_id, account_filter=None,
                                              allow_cache=False)
    for host in id_map.iterkeys():
        if vmid in id_map[host]:
            score = _calculate_vm_load(name_map[host])
            if score <= max_weight:
                retval = "OK"
            else:
                retval = "OVERLOADED"
    return retval


def get_vm_hostmap(dc_id, account_filter):
    """
    Given an optional account,
    Return a dictionary of VMs per host.
    """
    datalist = []
    id_map, name_map = retrieve_cloud_hostmap(dc_id, account_filter,
                                              allow_cache=True)
    for host in name_map.iterkeys():
        score = _calculate_vm_load(name_map[host])
        datalist.append(format_hostmap(host, score, ", ".join(name_map[host])))
    return json.dumps(datalist)
