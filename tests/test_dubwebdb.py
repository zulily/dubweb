#!/usr/bin/env python
"""
   Tests for dubwebdb.py
   Called via nosetests tests/test_dubwebdb.py
"""

# Global imports
import datetime
import calendar
import json
import unittest

# Local imports
from app import dubwebdb
from app import utils

SETTINGS_PATH = "/var/dubweb/.settings"

class TestDubwebDB(unittest.TestCase):
    """ Test the primary dubweb costing library """

    @classmethod
    def setUpClass(cls):
        settings = utils.load_json_definition_file(filename=SETTINGS_PATH)
        success, cls._conn = utils.open_monitoring_db(settings['dbhost'],
                                                      settings['dbuser'],
                                                      settings['dbpass'],
                                                      settings['db_db'])

    @classmethod
    def tearDownClass(cls):
        cls._conn.close()

    def test_all_get_providers(self):
        """ Test that all providers in MySQL have 3 fields"""
        providers = dubwebdb.get_providers(provider_id=None,
                                           dub_conn=self._conn)
        for pkey in providers.iterkeys():
            self.assertEquals(len(providers[pkey]), 3)


    def test_first_get_providers(self):
        """ Test the single provider retrieval from MySQL """
        provider = dubwebdb.get_providers(provider_id=1,
                                          dub_conn=self._conn)
        self.assertEquals(len(provider), 1)
        self.assertEquals(len(provider[1]), 3)


    def test_monthly_get_date_filters(self):
        """ Test the default monthly date retrieval, where
            start > Jan 1, 2014, and end > 3 months of seconds
            since start.  """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None,
                                               end_time=None)
        date_filters = dubwebdb.get_date_filters(default_monthly_time)
        jan_first = datetime.datetime(2014, 1, 1, 0, 0, 0)
        self.assertGreater(date_filters.start,
                           calendar.timegm(jan_first.timetuple()))
        self.assertGreater(date_filters.end,
                           date_filters.start + (3*29*24*60*60))


    def test_daily_get_date_filters(self):
        """ Test the default daily date retrieval, where
            start > Jan 1, 2014, and end > 29 days of seconds
            since start.  """
        default_daily_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                             start_time=None,
                                             end_time=None)
        date_filters = dubwebdb.get_date_filters(default_daily_time)
        jan_first = datetime.datetime(2014, 1, 1, 0, 0, 0)
        self.assertGreater(date_filters.start,
                           calendar.timegm(jan_first.timetuple()))
        self.assertGreater(date_filters.end,
                           date_filters.start + (29*24*60*60))

    def test_get_prv_metric_buckets(self):
        """ Test the metric bucketing mechanism, which
            groups, by provider, metric names so provider workloads
            (similar resources like VM_2proc, VM_4proc can be
            aggregated to a single VM bucket.  """
        buckets = dubwebdb.get_provider_metric_buckets(provider_id=1,
                                                       dub_conn=self._conn)
        for bucket_id in buckets.iterkeys():
            self.assertEqual(len(buckets[bucket_id]), 5)


    # CSV tests follow
    def test_csv_get_data_prv(self):
        """ Test the API used for dubwebdb monthly provider
            csv, returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None,
                                               end_time=None)
        all_prvs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_csv = dubwebdb.get_data_budget_provider(default_monthly_time,
                                                        all_prvs)
        for series in monthly_csv:
            self.assertEqual(len(series), 5)

    def test_custom_csv_get_data_prv(self):
        """ Test the API used for dubwebdb monthly provider
            csv, returning a 12 month dataset for one provider. """
        jan = datetime.datetime(2015, 1, 1, 0, 0, 0)
        jan_ts = calendar.timegm(jan.timetuple())
        december = datetime.datetime(2015, 12, 31, 23, 59, 0)
        dec_ts = calendar.timegm(december.timetuple())
        custom_time = dubwebdb.CTimes(d_format="%Y-%m",
                                      start_time=jan_ts,
                                      end_time=dec_ts)
        one_provider = dubwebdb.Ids(prv_id=1, team_id=None,
                                    project_id=None)
        csv_data = dubwebdb.get_data_budget_provider(custom_time,
                                                     one_provider)
        for series in csv_data:
            self.assertEqual(len(series), 14)

    def test_dflt_csv_get_data_team(self):
        """ Test the API used for dubwebdb monthly team csv,
            Returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None, end_time=None)
        all_prvs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_csv_data = dubwebdb.get_data_budget_team(default_monthly_time,
                                                         all_prvs)
        for series in monthly_csv_data:
            self.assertEqual(len(series), 5)

    def test_custom_csv_get_data_team(self):
        """ Test the API used for dubwebdb monthly team csv,
            Returning a 12 month dataset for one team. """
        jan = datetime.datetime(2015, 1, 1, 0, 0, 0)
        jan_ts = calendar.timegm(jan.timetuple())
        december = datetime.datetime(2015, 12, 31, 23, 59, 0)
        dec_ts = calendar.timegm(december.timetuple())
        custom_time = dubwebdb.CTimes(d_format="%Y-%m",
                                      start_time=jan_ts,
                                      end_time=dec_ts)
        one_team = dubwebdb.Ids(prv_id=None, team_id=1, project_id=None)
        csv_data = dubwebdb.get_data_budget_team(custom_time, one_team)
        for series in csv_data:
            self.assertEqual(len(series), 14)


    def test_cust_csv_get_data_team(self):
        """ Test the API used for dubwebdb monthly team csv,
            Returning a 1 month dataset for one provider. """
        decone = datetime.datetime(2015, 12, 1, 0, 0, 0)
        decone_ts = calendar.timegm(decone.timetuple())
        december = datetime.datetime(2015, 12, 31, 23, 59, 0)
        dec_ts = calendar.timegm(december.timetuple())
        custom_time = dubwebdb.CTimes(d_format="%Y-%m",
                                      start_time=decone_ts,
                                      end_time=dec_ts)
        one_prv = dubwebdb.Ids(prv_id=1, team_id=None, project_id=None)
        csv_data = dubwebdb.get_data_budget_team(custom_time, one_prv)
        for series in csv_data:
            self.assertEqual(len(series), 3)



    # Chart tests follow
    def test_mnth_get_data_prv(self):
        """ Test the API used for dubwebdb monthly provider
            chart, returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None, end_time=None)
        all_prvs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_chart_data = dubwebdb.get_data_provider(default_monthly_time,
                                                        all_prvs,
                                                        add_budget=True)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)


    def test_daily_get_data_prv(self):
        """ Test the API used for dubwebdb daily provider
            chart, returning the default (last 30 days) dataset. """
        default_daily_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                             start_time=None, end_time=None)
        all_prvs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        daily_chart_data = dubwebdb.get_data_provider(default_daily_time,
                                                      all_prvs, add_budget=True)
        for series in json.loads(daily_chart_data):
            self.assertEqual(len(series), 3)

    def test_monthly_get_data_team(self):
        """ Test the API used for dubwebdb monthly team
            chart, returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None, end_time=None)
        all_prvs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_chart_data = dubwebdb.get_data_team(default_monthly_time,
                                                    all_prvs, add_budget=True)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)

    def test_daily_get_data_team(self):
        """ Test the API used for dubwebdb daily team
            chart, returning the default (last 30 days) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                               start_time=None, end_time=None)
        all_prvs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_chart_data = dubwebdb.get_data_team(default_monthly_time,
                                                    all_prvs, add_budget=False)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)

    def test_mon_get_data_project(self):
        """ Test the API used for dubwebdb monthly project
            chart, returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None, end_time=None)
        all_prjs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_chart_data = dubwebdb.get_data_project(default_monthly_time,
                                                       all_prjs,
                                                       add_budget=True)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)

    def test_daily_get_data_project(self):
        """ Test the API used for dubwebdb daily project
            chart, returning the default (last 30 days) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                               start_time=None, end_time=None)
        all_prjs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_chart_data = dubwebdb.get_data_project(default_monthly_time,
                                                       all_prjs,
                                                       add_budget=False)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)

    def test_daily_get_data_workload(self):
        """ Test the API used for dubwebdb daily workload
            chart, returning the default (last 30 days) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                               start_time=None, end_time=None)
        one_prj = dubwebdb.Ids(prv_id=1, team_id=None, project_id=2)
        monthly_chart_data = dubwebdb.get_data_workload(default_monthly_time,
                                                        one_prj,
                                                        add_budget=False)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)


    def test_mon_estimate_data_provider(self):
        """ Test the API used for dubwebdb estimate monthly provider
            chart, returning the default (current, current + 1,
            current + 2)  dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None, end_time=None)
        all_prvs = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_data = dubwebdb.estimate_data_provider(default_monthly_time,
                                                       all_prvs,
                                                       add_budget=True)
        for series in json.loads(monthly_data):
            self.assertEqual(len(series), 3)


    def test_mon_estimate_data_team(self):
        """ Test the API used for dubwebdb estimate monthly team
            chart, returning the default (current, current + 1,
            current + 2)  dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                               start_time=None, end_time=None)
        all_teams = dubwebdb.Ids(prv_id=None, team_id=None, project_id=None)
        monthly_chart_data = dubwebdb.estimate_data_team(default_monthly_time,
                                                         all_teams,
                                                         add_budget=True)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)


if __name__ == "__main__":
    unittest.main()
