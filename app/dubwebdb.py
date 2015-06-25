#!/usr/bin/env python
"""
dubweb helper library
   Called by flask dubweb app
   to pull dubweb data, etc.

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

import datetime as dt
from dateutil.relativedelta import relativedelta
import time
import json
import app.utils as utils

from app import app

#globals
SETTINGS_FILE = "/var/dubweb/.settings"
#goog data lags by 2 days
LAG_SECONDS = 172800

class Ids(object):
    """
    Dubweb ids helper class
    """
    def __init__(self, prv_id, team_id, project_id):
        """
        Initial ids for chart
        """
        self.prv = prv_id
        self.team = team_id
        self.project = project_id

class CTimes(object):
    """
    Dubweb time-related helper class
    """
    def __init__(self, d_format, start_time, end_time):
        """
        Initial times for chart
        """
        self.dformat = d_format
        self.start = start_time
        self.end = end_time

def get_date_filters(my_time):
    """
    Given input type of months/days and either
       time_delta from current date, or
       optional start/end times in seconds since epoch
    Return start and endtimes since epoch
    """

    if my_time.dformat == "%Y-%m":
        if my_time.start is None or my_time.end is None:
            my_end_dt = dt.datetime.now() + relativedelta(day=31)
            my_time.end = int(my_end_dt.strftime('%s'))
            my_start_dt = my_end_dt + relativedelta(months=-3, days=+1)
            my_time.start = int(my_start_dt.strftime('%s'))
    else:
        # dformat is "%Y-%m-%d"
        if my_time.start is None or my_time.end is None:
            my_end_dt = dt.datetime.fromtimestamp((time.time() - LAG_SECONDS))
            my_time.end = int(my_end_dt.strftime('%s'))
            my_start_dt = my_end_dt + relativedelta(days=-30)
            my_time.start = int(my_start_dt.strftime('%s'))

    return my_time


def get_providers(provider_id, dub_conn):
    """
    Given provider id (of a datacenter instance) or None
    Return a dictionary of providers where
    you have name, lastetl, taxrate  for the given (or all) providers
    """

    prvdict = {}
    query_params = []

    query = """
            SELECT prvid, prvname, lastetl, taxrate FROM providers 
            """
    if provider_id is not None:
        query += " WHERE prvid = %s"
        query_params.append(str(provider_id))

    rows = None
    cursor = dub_conn.cursor()
    try:
        if query_params:
            cursor.execute(query, tuple(query_params))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            prvdict[row[0]] = [row[1], row[2], row[3]]
    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)
    finally:
        cursor.close()

    return prvdict

def get_teams(team_id, dub_conn):
    """
    Given team id or None
    Return key/value pairs of teamid : teamname
    for the given (or all) teams
    """

    teams = {}
    query_params = []

    query = """
            SELECT teamid, teamname FROM teams
            """
    if team_id is not None:
        query += " WHERE teamid = %s "
        query_params.append(str(team_id))

    cursor = dub_conn.cursor()
    try:
        if query_params:
            cursor.execute(query, tuple(query_params))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            teams[row[0]] = row[1]
    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)
    finally:
        cursor.close()

    return teams

def get_projects(provider_id, team_id, project_id, dub_conn):
    """
    Given provider,team, or project id or None
    Return dictionary of project id : external name, external id,
    provider id;  for the given (or all) teams
    """

    projectdict = {}
    query_params = []

    query = """
            SELECT prjid, extname, extid, prvid FROM projects WHERE 1
            """
    if provider_id is not None:
        query += " AND prvid = %s "
        query_params.append(str(provider_id))
    if team_id is not None:
        query += " AND teamid = %s "
        query_params.append(str(team_id))
    if project_id is not None:
        query += " AND prjid = %s"
        query_params.append(str(project_id))

    cursor = dub_conn.cursor()
    try:
        if query_params:
            cursor.execute(query, tuple(query_params))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            projectdict[row[0]] = [row[1], row[2], row[3]]
    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)
    finally:
        cursor.close()

    return projectdict

def get_budget_totals(ids, months, data_list, dub_conn):
    """
    Given optional filters for providers,team
    Return dubweb budget values by month.
    """

    query_params = []
    query = "SELECT month, CAST(IFNULL(sum(budget),0) AS SIGNED INT)"
    query += " FROM budgetdata WHERE 1 "
    if ids.team is not None:
        query += " AND teamid = %s "
        query_params.append(str(ids.team))
    if ids.prv is not None:
        query += " AND prvid = %s "
        query_params.append(str(ids.prv))
    query += " GROUP BY month"

    budget_list = utils.get_from_db(query, tuple(query_params), dub_conn)
    for budget in budget_list:
        if len(budget) > 0 and budget[1] is not None:
            if budget[0] not in months:
                continue
            data_point = {}
            data_point["Month"] = budget[0]
            data_point["Spend"] = int(budget[1])
            data_point["Budget"] = "Budget"
            data_list.append(data_point)

    return data_list


def get_data_provider(mytime, ids, add_budget):
    """
    Given a time, and optional filters for providers, team, project,
    Return dubweb values for each provider, by given time period.
    """
    providers = {}
    months = {}
    datalist = []
    query_params = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(mytime)
        providers = get_providers(ids.prv, dubconn)

        query = """
                   SELECT DATE_FORMAT(datetime,%s), prvid,
                   CAST(IFNULL(sum(cost),0) AS SIGNED INT) FROM metricdata
                   WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                   FROM_UNIXTIME(%s) """
        query_params.append(mytime.dformat)
        query_params.append(mytime.start)
        query_params.append(mytime.end)
        if ids.team is not None:
            query += " AND teamid = %s "
            query_params.append(str(ids.team))
        if ids.project is not None:
            query += " AND prjid = %s "
            query_params.append(str(ids.project))
        if ids.prv is not None:
            query += " AND prvid = %s "
            query_params.append(str(ids.prv))
        query += " GROUP BY prvid, DATE_FORMAT(datetime,%s)"
        query_params.append(mytime.dformat)

        dubmetrics = utils.get_from_db(query, query_params, dubconn)


        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[2] is not None:
                data_point = {}
                data_point["Month"] = dubmetric[0]
                data_point["Provider"] = providers[dubmetric[1]][0]
                data_point["Spend"] = dubmetric[2]
                datalist.append(data_point)
                months[dubmetric[0]] = 1

        if add_budget:
            datalist = get_budget_totals(ids, months, datalist, dubconn)


        dubconn.close()
    return json.dumps(datalist)

def get_data_team(mytime, ids, add_budget):
    """
    Given a time, and optional filters for providers, team, project,
    Return dubweb values for each team, by given time period.
    """
    teams = {}
    months = {}
    datalist = []
    query_params = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(mytime)
        teams = get_teams(ids.team, dubconn)

        query = """
                   SELECT DATE_FORMAT(datetime,%s), teamid,
                   CAST(IFNULL(sum(cost),0) AS SIGNED INT) FROM metricdata
                   WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                   FROM_UNIXTIME(%s) """
        query_params.append(mytime.dformat)
        query_params.append(mytime.start)
        query_params.append(mytime.end)
        if ids.team is not None:
            query += " AND teamid = %s "
            query_params.append(str(ids.team))
        if ids.project is not None:
            query += " AND prjid = %s "
            query_params.append(str(ids.project))
        if ids.prv is not None:
            query += " AND prvid = %s "
            query_params.append(str(ids.prv))
        query += " GROUP BY teamid, DATE_FORMAT(datetime,%s)"
        query_params.append(mytime.dformat)

        dubmetrics = utils.get_from_db(query, query_params, dubconn)


        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[2] is not None:
                data_point = {}
                data_point["Month"] = dubmetric[0]
                data_point["Team"] = teams[dubmetric[1]]
                data_point["Spend"] = dubmetric[2]
                datalist.append(data_point)
                months[dubmetric[0]] = 1

        if add_budget:
            datalist = get_budget_totals(ids, months, datalist, dubconn)


        dubconn.close()
    return json.dumps(datalist)

def get_data_project(mytime, ids, add_budget):
    """
    Given a time, and optional filters for providers, team, project,
    Return dubweb values for each project, by given time period.
    """
    projects = {}
    months = {}
    datalist = []
    query_params = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(mytime)
        projects = get_projects(ids.prv, ids.team, ids.project, dubconn)

        query = """
                   SELECT DATE_FORMAT(datetime,%s), prjid,
                   CAST(IFNULL(sum(cost),0) AS SIGNED INT) FROM metricdata
                   WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                   FROM_UNIXTIME(%s) """
        query_params.append(mytime.dformat)
        query_params.append(mytime.start)
        query_params.append(mytime.end)
        if ids.team is not None:
            query += " AND teamid = %s "
            query_params.append(str(ids.team))
        if ids.project is not None:
            query += " AND prjid = %s "
            query_params.append(str(ids.project))
        if ids.prv is not None:
            query += " AND prvid = %s "
            query_params.append(str(ids.prv))
        query += " GROUP BY prjid, DATE_FORMAT(datetime,%s)"
        query_params.append(mytime.dformat)

        dubmetrics = utils.get_from_db(query, query_params, dubconn)


        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[2] is not None:
                data_point = {}
                data_point["Month"] = dubmetric[0]
                data_point["Project"] = projects[dubmetric[1]][0]
                data_point["Spend"] = dubmetric[2]
                datalist.append(data_point)
                months[dubmetric[0]] = 1

        if add_budget:
            datalist = get_budget_totals(ids, months, datalist, dubconn)


        dubconn.close()
    return json.dumps(datalist)

