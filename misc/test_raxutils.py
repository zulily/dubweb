#!/usr/bin/env python
"""
   Tests for raxutils.py
   Called via nosetests tests/test_raxutils.py
"""

# Global imports
import unittest
import json
# Local imports
from app import raxutils

class TestRAXUtils(unittest.TestCase):
    """ Standard test class, for all utils functions """

    def test_retrieve_cloud_hostmap(self):
        """ Test retrieval from rackspace cloud api """
        ids, names = raxutils.retrieve_cloud_hostmap(dc_id='iad',
                                                     account_filter=None,
                                                     allow_cache=False)
        self.assertGreater(len(ids), 1)
        zm_id, zm_nm = raxutils.retrieve_cloud_hostmap(dc_id='iad',
                                                       account_filter='account_id_1',
                                                       allow_cache=False)
        for host in ids.iterkeys():
            self.assertGreaterEqual(len(ids[host]),
                                    len(zm_id[host]))
            self.assertGreaterEqual(len(names[host]),
                                    len(zm_nm[host]))

    def test_check_host_capacity(self):
        """ Test the API checking for overloaded vm """
        # allow standard weighting, checking known non-overloaded VM
        vmid = "replace_with_id"
        retval = raxutils.check_host_capacity(dc_id='iad', vmid=vmid,
                                              max_weight=None)
        self.assertEqual(retval, "OK")

        # now change weighting to allow
        retval = raxutils.check_host_capacity(dc_id='iad', vmid=vmid,
                                              max_weight=5)
        self.assertEqual(retval, "OVERLOADED")


    def test_get_vm_hostmap(self):
        """ Test the API charting VMs per host"""
        all_hosts = raxutils.get_vm_hostmap(dc_id='iad',
                                            account_filter=None)
        for host in json.loads(all_hosts):
            self.assertGreaterEqual(host['Load'], 1)


if __name__ == "__main__":
    unittest.main()
