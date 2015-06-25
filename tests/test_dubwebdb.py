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

class TestDubwebDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings = utils.load_json_definition_file(
                            filename="/var/dubweb/.settings")
        success, cls._conn = utils.open_monitoring_db(
                                     settings['dbhost'],
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


    def test_monthly_default_get_date_filters(self):
        """ Test the default monthly date retrieval, where
            start > Jan 1, 2014, and end > 3 months of seconds
            since start.  """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                    start_time=None, end_time=None)
        date_filters = dubwebdb.get_date_filters(default_monthly_time)
        jan_first = datetime.datetime(2014, 1, 1, 0, 0, 0)
        self.assertGreater(date_filters.start,
                           calendar.timegm(jan_first.timetuple()))
        self.assertGreater(date_filters.end,
                           date_filters.start + (3*29*24*60*60))


    def test_daily_default_get_date_filters(self):
        """ Test the default daily date retrieval, where
            start > Jan 1, 2014, and end > 29 days of seconds
            since start.  """
        default_daily_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                    start_time=None, end_time=None)
        date_filters = dubwebdb.get_date_filters(default_daily_time)
        jan_first = datetime.datetime(2014, 1, 1, 0, 0, 0)
        self.assertGreater(date_filters.start,
                           calendar.timegm(jan_first.timetuple()))
        self.assertGreater(date_filters.end,
                           date_filters.start + (29*24*60*60))

    def test_monthly_default_get_data_provider(self):
        """ Test the API used for dubwebdb monthly provider
            chart, returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                    start_time=None, end_time=None)
        all_providers_projects_teams = dubwebdb.Ids(
                                         prv_id=None, team_id=None,
                                         project_id=None)
        monthly_chart_data = dubwebdb.get_data_provider(
                                         default_monthly_time,
                                         all_providers_projects_teams,
                                         add_budget=True)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)


    def test_daily_default_get_data_provider(self):
        """ Test the API used for dubwebdb daily provider
            chart, returning the default (last 30 days) dataset. """
        default_daily_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                    start_time=None, end_time=None)
        all_providers_projects_teams = dubwebdb.Ids(
                                         prv_id=None, team_id=None,
                                         project_id=None)
        daily_chart_data = dubwebdb.get_data_provider(
                                         default_daily_time,
                                         all_providers_projects_teams,
                                         add_budget=True)
        for series in json.loads(daily_chart_data):
            self.assertEqual(len(series), 3)

    def test_monthly_default_get_data_team(self):
        """ Test the API used for dubwebdb monthly team
            chart, returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                    start_time=None, end_time=None)
        all_providers_projects_teams = dubwebdb.Ids(
                                         prv_id=None, team_id=None,
                                         project_id=None)
        monthly_chart_data = dubwebdb.get_data_team(
                                         default_monthly_time,
                                         all_providers_projects_teams,
                                         add_budget=True)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)

    def test_daily_default_get_data_team(self):
        """ Test the API used for dubwebdb daily team
            chart, returning the default (last 30 days) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                    start_time=None, end_time=None)
        all_providers_projects_teams = dubwebdb.Ids(
                                         prv_id=None, team_id=None,
                                         project_id=None)
        monthly_chart_data = dubwebdb.get_data_team(
                                         default_monthly_time,
                                         all_providers_projects_teams,
                                         add_budget=False)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)

    def test_monthly_default_get_data_project(self):
        """ Test the API used for dubwebdb monthly project
            chart, returning the default (last 3 months) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m",
                                    start_time=None, end_time=None)
        all_providers_projects_teams = dubwebdb.Ids(
                                         prv_id=None, team_id=None,
                                         project_id=None)
        monthly_chart_data = dubwebdb.get_data_project(
                                         default_monthly_time,
                                         all_providers_projects_teams,
                                         add_budget=True)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)

    def test_daily_default_get_data_project(self):
        """ Test the API used for dubwebdb daily project 
            chart, returning the default (last 30 days) dataset. """
        default_monthly_time = dubwebdb.CTimes(d_format="%Y-%m-%d",
                                    start_time=None, end_time=None)
        all_providers_projects_teams = dubwebdb.Ids(
                                         prv_id=None, team_id=None,
                                         project_id=None)
        monthly_chart_data = dubwebdb.get_data_project(
                                         default_monthly_time,
                                         all_providers_projects_teams,
                                         add_budget=False)
        for series in json.loads(monthly_chart_data):
            self.assertEqual(len(series), 3)


if __name__ == "__main__":
    unittest.main()
