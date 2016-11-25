#!/usr/bin/env python
"""
   Tests for capdb.py
   Called via nosetests tests/test_capdb.py
"""

# Global imports
import calendar
import datetime
import json
import unittest

# Local imports
from app import capdb
from app import utils

class TestCapDB(unittest.TestCase):
    """ Test for the capacity db functions"""

    @classmethod
    def setUpClass(cls):
        settings = utils.load_json_definition_file(filename=\
                                                   "/var/dubweb/.cap_settings")
        success, cls._conn = utils.open_monitoring_db(settings['cdbhost'],
                                                      settings['cdbuser'],
                                                      settings['cdbpass'],
                                                      settings['cdb_db'])

    @classmethod
    def tearDownClass(cls):
        cls._conn.close()

    def test_all_get_capmetrics(self):
        """ Test that all capmetrics in MySQL have 4 fields"""
        capmetrics = capdb.get_cap_ids(cap_ids=None,
                                       cap_conn=self._conn)
        for capkey in capmetrics.iterkeys():
            self.assertEquals(len(capmetrics[capkey]), 5)


    def test_first_get_capmetrics(self):
        """ Test the single capmetric retrieval from MySQL """
        capmetric = capdb.get_cap_ids(cap_ids="1",
                                      cap_conn=self._conn)
        self.assertEquals(len(capmetric), 1)
        self.assertEquals(len(capmetric['1']), 5)

    def test_default_driver_metric(self):
        """ Test the single capmetric retrieval from MySQL """
        metric = capdb.get_driver_metric(source_metric=50,
                                         my_date=None)
        self.assertGreater(metric, 1500000)

    def test_custom_driver_metric(self):
        """ Test the single capmetric retrieval from MySQL """
        jan = datetime.datetime(2016, 1, 1, 0, 0, 0)
        jan_ts = calendar.timegm(jan.timetuple())
        metric = capdb.get_driver_metric(source_metric=50,
                                         my_date=jan_ts)
        self.assertGreater(metric, 1500000)

    # Chart tests follow
    def test_get_capacity_daily(self):
        """ Test the API used for daily capdb capacity chart. """

        daily_chart_data = capdb.get_capacity_daily(ids=None,
                                                    add_limits=False)
        for series in json.loads(daily_chart_data):
            self.assertEqual(len(series), 3)

    def test_default_monitor_daily(self):
        """ Test the API used for daily capacity monitor value. """

        daily_chart_data = capdb.get_monitor_daily(ids=None,
                                                   opt_date=None)
        for series in json.loads(daily_chart_data):
            self.assertEqual(len(series), 3)

    def test_custom_monitor_daily(self):
        """ Test the API used for specific capacity monitor value. """

        jan = datetime.datetime(2016, 1, 1, 0, 0, 0)
        jan_ts = calendar.timegm(jan.timetuple())
        daily_chart_data = capdb.get_monitor_daily(ids=None,
                                                   opt_date=jan_ts)
        for series in json.loads(daily_chart_data):
            self.assertEqual(len(series), 3)

    def test_default_capacity_model(self):
        """ Test the API used for generating capacity projections. """

        model_json_string = capdb.get_capacity_model(ids="1",
                                                     opt_date=None)
        model_data = json.loads(model_json_string)
        self.assertEqual(len(model_data['1']['coef']), 1)
        self.assertGreater(len(model_data['1']['model']), 1023)
        self.assertGreater(model_data['1']['driver'], 1500000) 

    def test_custom_capacity_model(self):
        """ Test the API used for generating capacity projections. """

        jan = datetime.datetime(2016, 1, 1, 0, 0, 0)
        jan_ts = calendar.timegm(jan.timetuple())
        model_json_string = capdb.get_capacity_model(ids="1",
                                                     opt_date=jan_ts)
        model_data = json.loads(model_json_string)
        self.assertEqual(len(model_data['1']['coef']), 1)
        self.assertGreater(len(model_data['1']['model']), 1023) 
        self.assertGreater(model_data['1']['driver'], 1500000) 

if __name__ == "__main__":
    unittest.main()
