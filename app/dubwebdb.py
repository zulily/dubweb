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
from collections import defaultdict, OrderedDict
import time
import json
import app.utils as utils
import re
import numpy as np

from app import app

#globals
SETTINGS_FILE = "/var/dubweb/.settings"
#goog data lags by 2 days
LAG_SECONDS = 172800
DEFAULT_FORECAST_PERIOD = 3 * 29 * 86400

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
            my_start_dt = my_end_dt + relativedelta(months=-3)
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


def get_budget_by_providers(ids, months, data_list, names, dub_conn):
    """
    Given optional filters for providers and team
    Return dubweb budget values by provider and month.
    """

    query_params = []
    query = "SELECT month, CAST(IFNULL(sum(budget),0) AS SIGNED INT), prvid"
    query += " FROM budgetdata WHERE 1 "
    if ids.team is not None:
        query += " AND teamid = %s "
        query_params.append(str(ids.team))
    if ids.prv is not None:
        query += " AND prvid = %s "
        query_params.append(str(ids.prv))
    query += " GROUP BY prvid, month"

    budget_list = utils.get_from_db(query, tuple(query_params), dub_conn)
    for budget in budget_list:
        if len(budget) > 0 and budget[1] is not None:
            if budget[0] not in months:
                continue
            data_point = {}
            data_point["Month"] = budget[0]
            data_point["Spend"] = int(budget[1])
            data_point["Budget"] = names[budget[2]][0]
            data_list.append(data_point)

    return data_list


def get_budget_by_teams(ids, months, data_list, names, dub_conn):
    """
    Given optional filters for providers and team
    Return dubweb budget values by team and month.
    """

    query_params = []
    query = "SELECT month, CAST(IFNULL(sum(budget),0) AS SIGNED INT), teamid"
    query += " FROM budgetdata WHERE 1 "
    if ids.team is not None:
        query += " AND teamid = %s "
        query_params.append(str(ids.team))
    if ids.prv is not None:
        query += " AND prvid = %s "
        query_params.append(str(ids.prv))
    query += " GROUP BY teamid, month"

    budget_list = utils.get_from_db(query, tuple(query_params), dub_conn)
    for budget in budget_list:
        if len(budget) > 0 and budget[1] is not None:
            if budget[0] not in months:
                continue
            data_point = {}
            data_point["Month"] = budget[0]
            data_point["Spend"] = int(budget[1])
            data_point["Budget"] = names[budget[2]]
            data_list.append(data_point)

    return data_list

def get_provider_metric_buckets(provider_id, dub_conn):
    """
    Given provider id (of a datacenter instance)
    Return a dictionary of metrics where, for a given metric,
    you have ruleid/bucket, groupname, textmatch, scalefactor, scaleunit.
    """

    ruledict = OrderedDict()
    metricbuckets = {}
    query_params = []

    query = """
            SELECT ruleid, groupname, textmatch,
            scalefactor, scaleunit FROM matchrules
            WHERE prvid = %s
            ORDER BY rank ASC 
            """
    query_params.append(str(provider_id))

    rows = None
    cursor = dub_conn.cursor()
    try:
        cursor.execute(query, tuple(query_params))
        rows = cursor.fetchall()
        for ruleid, groupname, textmatch, scalefactor, scaleunit in rows:
            ruledict[ruleid] = [int(ruleid), groupname, textmatch,
                                scalefactor, scaleunit]
    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)

    query = """
            SELECT metricid, metricname 
            FROM metrictypes WHERE prvid = %s
            """
    rows = None
    try:
        cursor.execute(query, tuple(query_params))
        rows = cursor.fetchall()
        for row in rows:
            metricbuckets[row[0]] = row[1]
    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)

    for metric_id in metricbuckets.iterkeys():
        for rule_id in ruledict.keys():
            if re.match(ruledict[rule_id][2], metricbuckets[metric_id]):
                metricbuckets[metric_id] = ruledict[rule_id]
                break

    return metricbuckets

def compute_month_stats(slice_len, stat_array):
    """
    Calculate statistics on a given (monthly) array.
    Return calculated statistics.
    """
    sdict = {}
    sdict['avg'] = np.mean(stat_array)
    sdict['len'] = len(stat_array)
    sdict['std'] = np.std(stat_array)
    if not slice_len:
        slice_len = sdict['len']
    sdict['slice_avg'] = np.mean(stat_array[:slice_len-1])
    sdict['slice_len'] = len(stat_array[:slice_len-1])

    return sdict

def forecast_metrics(times, my_id, current, prev):
    """
    Given a set of calculated statistics for current
    (and optionally previous) month,
    Return projected monthly values for each provider.
    """
    stats_list = []
    decay = 1.0

    if prev:
        trend = current['slice_avg'] / prev['slice_avg']
        if trend < 0:
            decay = -1.0
    else:
        trend = 1.0
    forecast = dt.datetime.fromtimestamp(float(times.start))
    endtime = dt.datetime.fromtimestamp(float(times.end))
    firstofmonth = dt.datetime.now() + relativedelta(day=1)
    if not prev or current['std'] == 0.0:
        dailyspend = current['avg']
    else:
        dailyspend = prev['avg']

    while forecast < endtime:
        forecast = forecast + relativedelta(day=1, months=+1, days=-1)
        daycount = int(forecast.strftime('%d'))
        month = forecast.strftime('%Y-%m')
        monthly_estimate = int(dailyspend * daycount)
        # Don't show estimated data from the past
        if forecast > firstofmonth:
            stats_list.append([month, my_id, monthly_estimate])
        forecast = forecast + relativedelta(days=+1)
        dailyspend *= trend
        # Allow trend to decay over time
        trend = (trend + decay + decay) / 3.0

    return stats_list

def estimate_monthly_metrics(my_time, d_metrics):
    """
    Given a forecast interval (using the time end)
    and a set of daily metrics,
    Return projected monthly metrics for each id.
    """
    metdict = {}
    prevmon = None

    # separate daily metrics into array
    for metric in d_metrics:
        if metric[1] not in metdict:
            metdict[metric[1]] = OrderedDict()
        if metric[0] not in metdict[metric[1]]:
            metdict[metric[1]][metric[0]] = []
        metdict[metric[1]][metric[0]].append(metric[2])
    d_metrics = []

    # calculate data needed for forecasting, by id
    for m_id in metdict.iterkeys():
        if len(metdict[m_id].keys()) > 1:
            prevmon = metdict[m_id].keys()[-2]
        curmon = metdict[m_id].keys()[-1]
        curmon_dt = dt.datetime.strptime(curmon + '-01T00:00:00',
                                         '%Y-%m-%dT%H:%M:%S')
        my_time.start = int(curmon_dt.strftime('%s'))
        if my_time.end < (my_time.start + DEFAULT_FORECAST_PERIOD):
            my_time.end = int((curmon_dt + \
                              relativedelta(months=3)).strftime('%s'))
        curstdict = {}
        prevdict = {}
        curstdict = compute_month_stats(None,
                                        np.array(metdict[m_id][curmon]))
        if m_id in metdict and prevmon in metdict[m_id]:
            prevdict = compute_month_stats(curstdict['len'],
                                           np.array(metdict[m_id][prevmon]))
        # forecast, based on id
        d_metrics += forecast_metrics(my_time, m_id, curstdict,
                                      prevdict)

    return d_metrics


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
            datalist = get_budget_by_providers(ids, months, datalist,
                                               providers, dubconn)


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
            datalist = get_budget_by_teams(ids, months, datalist,
                                           teams, dubconn)


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

        dubconn.close()
    return json.dumps(datalist)

def get_data_workload(mytime, ids, add_budget):
    """
    Given a time, provider and project,
    Return dubweb values for each workload, by given time period.
    """
    buckets = {}
    met_sums = defaultdict(dict)
    datalist = []
    query_params = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(mytime)
        buckets = get_provider_metric_buckets(ids.prv, dubconn)

        query = """
                   SELECT DATE_FORMAT(datetime,%s), metric,
                   CAST(IFNULL(sum(cost),0) AS SIGNED INT) FROM metricdata
                   WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                   FROM_UNIXTIME(%s) AND prvid = %s AND prjid = %s 
                   GROUP BY metric, DATE_FORMAT(datetime,%s) """
        query_params.append(mytime.dformat)
        query_params.append(mytime.start)
        query_params.append(mytime.end)
        query_params.append(str(ids.prv))
        query_params.append(str(ids.project))
        query_params.append(mytime.dformat)

        dubmetrics = utils.get_from_db(query, query_params, dubconn)

        # Group metrics per day, bucket
        for dubmetric in dubmetrics:
            if dubmetric[2] != 0:
                try:
                    met_sums[dubmetric[0]][buckets[dubmetric[1]][0]][0] = \
                     met_sums[dubmetric[0]][buckets[dubmetric[1]][0]][0] + \
                     dubmetric[2]
                except KeyError:
                    met_sums[dubmetric[0]][buckets[dubmetric[1]][0]] = \
                       [dubmetric[2], buckets[dubmetric[1]][1]]

        for day, metrics in met_sums.iteritems():
            for metval in metrics.iterkeys():
                data_point = {}
                data_point["Month"] = day
                data_point["Workload"] = metrics[metval][1]
                data_point["Spend"] = int(metrics[metval][0])
                datalist.append(data_point)

    dubconn.close()

    return json.dumps(datalist)


def estimate_data_provider(mytime, ids, add_budget):
    """
    Given a time, and optional filters for providers, team, project,
    Estimate (where necessary) and return dubweb values for each provider,
    by given time period.
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
        def_time = CTimes(d_format="%Y-%m", start_time=None, end_time=None)
        def_time = get_date_filters(def_time)
        providers = get_providers(ids.prv, dubconn)

        query = """
                   SELECT DATE_FORMAT(datetime,%s), prvid,
                   CAST(IFNULL(sum(cost),0) AS SIGNED INT) FROM metricdata
                   WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                   FROM_UNIXTIME(%s) """
        query_params.append(def_time.dformat)
        query_params.append(def_time.start)
        query_params.append(def_time.end)
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
        query_params.append("%Y-%m-%d")

        dailymetrics = utils.get_from_db(query, query_params, dubconn)

        dubmetrics = estimate_monthly_metrics(mytime, dailymetrics)

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[2] is not None:
                data_point = {}
                data_point["Month"] = dubmetric[0]
                data_point["Provider"] = providers[dubmetric[1]][0]
                data_point["Spend"] = dubmetric[2]
                datalist.append(data_point)
                months[dubmetric[0]] = 1

        if add_budget:
            datalist = get_budget_by_providers(ids, months, datalist,
                                               providers, dubconn)


        dubconn.close()
    return json.dumps(datalist)

def estimate_data_team(mytime, ids, add_budget):
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
        def_time = CTimes(d_format="%Y-%m", start_time=None, end_time=None)
        def_time = get_date_filters(def_time)
        teams = get_teams(ids.team, dubconn)

        query = """
                   SELECT DATE_FORMAT(datetime,%s), teamid,
                   CAST(IFNULL(sum(cost),0) AS SIGNED INT) FROM metricdata
                   WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                   FROM_UNIXTIME(%s) """
        query_params.append(def_time.dformat)
        query_params.append(def_time.start)
        query_params.append(def_time.end)
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
        query_params.append("%Y-%m-%d")

        dailymetrics = utils.get_from_db(query, query_params, dubconn)

        dubmetrics = estimate_monthly_metrics(mytime, dailymetrics)

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[2] is not None:
                data_point = {}
                data_point["Month"] = dubmetric[0]
                data_point["Team"] = teams[dubmetric[1]]
                data_point["Spend"] = dubmetric[2]
                datalist.append(data_point)
                months[dubmetric[0]] = 1

        if add_budget:
            datalist = get_budget_by_teams(ids, months, datalist,
                                           teams, dubconn)


        dubconn.close()
    return json.dumps(datalist)

