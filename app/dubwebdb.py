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
from collections import defaultdict, OrderedDict
import json
import re
import time
import numpy as np
from dateutil import parser
from dateutil.relativedelta import relativedelta
from app import app
import app.utils as utils

#globals
SETTINGS_FILE = "/var/dubweb/.settings"
#goog data lags by 2 days
LAG_SECONDS = 172800
DEFAULT_FORECAST_PERIOD = 3 * 29 * 86400

class Ids(object):
    """
    Dubweb ids helper class
    """
    def __init__(self, prv_id, team_id, project_id, div_id):
        """
        Initial ids for chart
        """
        self.prv = prv_id
        self.team = team_id
        self.project = project_id
        self.div = div_id

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
    Return start and endtimes since epoch
    """

    if my_time.dformat == "%Y-%m":
        if my_time.start is None or my_time.end is None:
            my_end_dt = dt.datetime.now() + relativedelta(day=31)
            my_time.end = int(my_end_dt.strftime('%s'))
            my_start_dt = my_end_dt + relativedelta(months=-3, day=31)
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
    Return a dictionary of providers where
    you have name, lastetl, taxrate  for the given (or all) providers
    """

    prvdict = {}
    query_params = []

    query = """
            SELECT prvid, prvname, lastetl, taxrate FROM providers 
            """
    if provider_id is not None:
        myformat = ','.join(['%s'] * len(provider_id)) + ')'
        query += " WHERE prvid IN ("
        query += myformat
        for prv_val in provider_id:
            query_params.append(int(prv_val))

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

def get_teams(team_ids, dub_conn):
    """
    Return key/value pairs of teamid : teamname
    for the given (or all) teams
    """

    teams = {}
    query_params = []

    query = """
            SELECT teamid, teamname FROM teams WHERE 1
            """
    if team_ids is not None:
        myformat = ','.join(['%s'] * len(team_ids)) + ')'
        query += " AND teamid IN ("
        query += myformat
        for teamval in team_ids:
            query_params.append(int(teamval))
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

def lookup_divisions(team_ids, dub_conn):
    """
    Return key/value pairs of teamid : divisionid
    for the given (or all) teams
    """

    teams = {}
    query_params = []

    query = """
            SELECT teamid, divid FROM teams WHERE 1
            """
    if team_ids is not None:
        myformat = ','.join(['%s'] * len(team_ids)) + ')'
        query += " AND teamid IN ("
        query += myformat
        for teamval in team_ids:
            query_params.append(int(teamval))
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

def set_teams_from_divs(ids, dub_conn):
    """
    Given an ID class with one or more divisions set,
    return the ID class with the appropriate teams set,
    with all teams, if no division is set.
    """

    query_params = []

    query = """
            SELECT distinct teamid FROM teams WHERE 1
            """
    if ids.div is not None:
        myformat = ','.join(['%s'] * len(ids.div)) + ')'
        query += " AND divid IN ("
        query += myformat
        for divval in ids.div:
            query_params.append(int(divval))
    cursor = dub_conn.cursor()
    try:
        if query_params:
            cursor.execute(query, tuple(query_params))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        ids.team = [str(row[0]) for row in rows]

    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)
    finally:
        cursor.close()

    return ids

def get_divisions(div_ids, dub_conn):
    """
    Return key/value pairs of divid : divname
    for the given (or all) divisions
    """

    divisions = {}
    query_params = []

    query = """
            SELECT divid, divname FROM divisions WHERE 1
            """
    if div_ids is not None:
        myformat = ','.join(['%s'] * len(div_ids)) + ')'
        query += " AND divid IN ("
        query += myformat
        for divval in div_ids:
            query_params.append(int(divval))
    cursor = dub_conn.cursor()
    try:
        if query_params:
            cursor.execute(query, tuple(query_params))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            divisions[row[0]] = row[1]
    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)
    finally:
        cursor.close()

    return divisions

def get_projects(provider_id, team_ids, project_id, dub_conn):
    """
    Return dictionary of project id : external name, external id,
    provider id;  for the given (or all) teams
    """

    projectdict = {}
    query_params = []

    query = """
            SELECT prjid, extname, extid, prvid FROM projects WHERE 1
            """
    if provider_id is not None:
        myformat = ','.join(['%s'] * len(provider_id)) + ')'
        query += " AND prvid IN ("
        query += myformat
        for prv_val in provider_id:
            query_params.append(int(prv_val))
    if team_ids is not None:
        myformat = ','.join(['%s'] * len(team_ids)) + ')'
        query += " AND teamid IN ("
        query += myformat
        for teamval in team_ids:
            query_params.append(int(teamval))
    if project_id is not None:
        query += " AND prjid = %s"
        query_params.append(int(project_id))

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


def get_budget_by_providers(ids, dub_conn):
    """
    Return dubweb budget values by provider and month.
    """

    query_params = []
    query = "SELECT month, CAST(IFNULL(sum(budget),0) AS SIGNED INT), prvid"
    query += " FROM budgetdata WHERE 1 "
    if ids.team is not None:
        myformat = ','.join(['%s'] * len(ids.team)) + ')'
        query += " AND teamid IN ("
        query += myformat
        for teamval in ids.team:
            query_params.append(int(teamval))
    if ids.prv is not None:
        myformat = ','.join(['%s'] * len(ids.prv)) + ')'
        query += " AND prvid IN ("
        query += myformat
        for prv_val in ids.prv:
            query_params.append(int(prv_val))
    query += " GROUP BY prvid, month"

    return utils.get_from_db(query, tuple(query_params), dub_conn)


def get_response_dict(ids, dub_conn):
    """
    Return dubweb budget responses by team, provider, month.
    """

    query_params = []
    data_points = defaultdict(lambda: defaultdict(dict))
    query = """SELECT teamid, prv.prvname, month, response
               FROM budgetdata 
               JOIN providers AS prv ON budgetdata.prvid = prv.prvid
               WHERE 1
            """
    if ids.team is not None:
        myformat = ','.join(['%s'] * len(ids.team)) + ')'
        query += " AND teamid IN ("
        query += myformat
        for teamval in ids.team:
            query_params.append(int(teamval))
    if ids.prv is not None:
        myformat = ','.join(['%s'] * len(ids.prv)) + ')'
        query += " AND budgetdata.prvid IN ("
        query += myformat
        for prv_val in ids.prv:
            query_params.append(int(prv_val))
    responses = utils.get_from_db(query, tuple(query_params), dub_conn)
    for row in responses:
        data_points[row[0]][row[1]][row[2]] = row[3]

    return data_points


def date_in_range(date_str, start_ts, end_ts):
    """
    Return True if month is between the timestamps.
    """
    curdate = parser.parse(date_str + "-01 00:00:00")
    cur_ts = time.mktime(curdate.timetuple())
    if int(start_ts) <= cur_ts <= int(end_ts):
        return True
    else:
        return False

def get_budget_provider_dict(ids, start_ts, end_ts, dub_conn):
    """
    Return dubweb chart series by provider and month.
    """
    months = {}
    data_points = defaultdict(dict)
    providers = get_providers(ids.prv, dub_conn)
    budget_list = get_budget_by_providers(ids, dub_conn)
    for budget in budget_list:
        if date_in_range(budget[0], start_ts, end_ts):
            data_points[providers[budget[2]][0]][budget[0]] = int(budget[1])
            months[budget[0]] = 1

    return data_points, sorted(months.keys())


def get_budget_team_dict(ids, start_ts, end_ts, dub_conn):
    """
    Return dubweb budget dictionary by team and month.
    """
    months = {}
    data_points = defaultdict(dict)
    teams = get_teams(ids.team, dub_conn)
    budget_list = get_budget_by_teams(ids, dub_conn)
    for budget in budget_list:
        if date_in_range(budget[0], start_ts, end_ts):
            data_points[teams[budget[2]]][budget[0]] = int(budget[1])
            months[budget[0]] = 1

    return data_points, sorted(months.keys())

def get_budget_div_dict(ids, my_time, divs, t_divs, dub_conn):
    """
    Return dubweb budget dictionary by division and month.
    """
    months = {}
    datapts = defaultdict(lambda: defaultdict(int))
    budget_list = get_budget_by_teams(ids, dub_conn)
    for bgt in budget_list:
        if date_in_range(bgt[0], my_time.start, my_time.end):
            datapts[divs[t_divs[bgt[2]]]][bgt[0]] += int(bgt[1])
            months[bgt[0]] = 1

    return datapts, sorted(months.keys())


def add_budget_series_providers(ids, months, data_list, names, dub_conn):
    """
    Return dubweb chart series by provider and month.
    """

    budget_list = get_budget_by_providers(ids, dub_conn)
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


def get_budget_by_teams(ids, dub_conn):
    """
    Return dubweb budget values by team and month.
    """

    query_params = []
    query = "SELECT month, CAST(IFNULL(sum(budget),0) AS SIGNED INT), teamid"
    query += " FROM budgetdata WHERE 1 "
    if ids.team is not None:
        myformat = ','.join(['%s'] * len(ids.team)) + ')'
        query += " AND teamid IN ("
        query += myformat
        for teamval in ids.team:
            query_params.append(int(teamval))
    if ids.prv is not None:
        myformat = ','.join(['%s'] * len(ids.prv)) + ')'
        query += " AND prvid IN ("
        query += myformat
        for prv_val in ids.prv:
            query_params.append(int(prv_val))
    query += " GROUP BY teamid, month"

    return utils.get_from_db(query, tuple(query_params), dub_conn)

def add_budget_series_teams(ids, months, data_list, names, dub_conn):
    """
    Return dubweb budget chart series by team and month.
    """

    budget_list = get_budget_by_teams(ids, dub_conn)
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

def add_budget_series_divisions(ids, months, data_list, divisions,
                                team_divs, dub_conn):
    """
    Return dubweb budget chart series by division and month.
    """

    budget_list = defaultdict(lambda: defaultdict(int))
    t_budgets = get_budget_by_teams(ids, dub_conn)
    for t_bgt in t_budgets:
        if t_bgt[1] is not None:
            # sum across divisions
            budget_list[team_divs[t_bgt[2]]][t_bgt[0]] += int(t_bgt[1])

    for div in budget_list:
        for month in budget_list[div]:
            if month not in months:
                continue
            if budget_list[div][month] > 0:
                data_point = {}
                data_point["Month"] = month
                data_point["Spend"] = budget_list[div][month]
                data_point["Budget"] = divisions[div]
                data_list.append(data_point)

    return data_list

def get_provider_metric_buckets(provider_id, dub_conn):
    """
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
    query_params.append(int(provider_id))

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
    Return calculated statistics.
    """
    sdict = {}
    sdict['avg'] = np.mean(stat_array)
    sdict['len'] = len(stat_array)
    sdict['std'] = np.std(stat_array)
    if not slice_len:
        slice_len = sdict['len']
    sdict['slice_avg'] = np.mean(stat_array[:slice_len])
    sdict['slice_len'] = len(stat_array[:slice_len])

    return sdict

def forecast_metrics(times, my_id, current, prev):
    """
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


def gen_item_table(data_set, header_row, inc_total, sum_col):
    """
        Return a list of lists with each 'cell' of a csv table.
    """
    datarow = []
    datalist = []

    # Construct header row
    datalist.append(header_row)

    # Parse into table, adding subtotals
    total = 0
    for row in data_set:
        datarow = list(row)
        if inc_total:
            try:
                value = row[sum_col]
            except KeyError:
                value = 0
            total += value
        datalist.append(datarow)

    lastrow = [None]*len(datarow)
    if inc_total:
        lastrow[0] = "Total:"
        lastrow[sum_col] = total
    datalist.append(lastrow)
    return datalist

def gen_cost_table(data_set, month_arr, table_str):
    """
        Return a list of lists with each 'cell' of a csv table.
    """
    monthvals = {}
    datarow = []
    datalist = []

    # Construct header row
    datarow = [table_str]
    datarow.extend(month_arr)
    datarow.extend(["Subtotal"])
    datalist.append(datarow)

    # Parse into table, adding subtotals
    for p_key in data_set.iterkeys():
        datarow = [p_key]
        data_sum = 0
        for month in month_arr:
            try:
                value = int(data_set[p_key][month])
            except KeyError:
                value = 0
            datarow.extend([value])
            data_sum += value
            try:
                monthvals[month] += value
            except KeyError:
                monthvals[month] = value
        datarow.extend([data_sum])
        datalist.append(datarow)

    # Add subtotals
    datarow = ["Totals"]
    total = 0
    for month in month_arr:
        try:
            total += monthvals[month]
            datarow.extend([monthvals[month]])
        except KeyError:
            datarow.extend([0])
    datarow.extend([total])
    datalist.append(datarow)
    nullrow = [None]*len(datarow)
    datalist.append(nullrow)

    return datalist


def gen_over_under_table(data_set, ids, mytime, dubconn, table_str):
    """
        Return a list of lists with each 'cell' of an over/under csv table.
    """
    monthvals = {}
    monthbudgets = {}
    monthoverunders = {}
    datarow = []
    datalist = []

    budgets, month_arr = get_budget_provider_dict(ids, int(mytime.start),
                                                  int(mytime.end), dubconn)
    responses = get_response_dict(ids, dubconn)
    # Construct header row
    datarow = [table_str]
    for month in month_arr:
        datarow.extend([month + " Actuals"])
        datarow.extend([month + " Budget"])
        datarow.extend([month + " Over/(-)Under Budget"])
        datarow.extend([month + " Response"])
    datarow.extend(["Subtotal"])
    datalist.append(datarow)

    # construct actual, over_under, and response, adding subtotals
    for p_key in data_set.iterkeys():
        datarow = [p_key]
        data_sum = 0
        for month in month_arr:
            try:
                value = int(data_set[p_key][month])
            except KeyError:
                value = 0
            datarow.extend([value])
            data_sum += value
            try:
                budget = int(budgets[p_key][month])
            except KeyError:
                budget = 0
            datarow.extend([budget])
            overunder = value - budget
            datarow.extend([overunder])
            try:
                response = responses[int(ids.team[0])][p_key][month]
            except KeyError:
                response = None
            datarow.extend([response])
            try:
                monthvals[month] += value
            except KeyError:
                monthvals[month] = value
            try:
                monthbudgets[month] += budget
            except KeyError:
                monthbudgets[month] = budget
            try:
                monthoverunders[month] += overunder
            except KeyError:
                monthoverunders[month] = overunder
        datarow.extend([data_sum])
        datalist.append(datarow)

    # Add subtotals
    datarow = ["Totals"]
    total = 0
    for month in month_arr:
        try:
            total += monthvals[month]
            datarow.extend([monthvals[month], monthbudgets[month],
                            monthoverunders[month], None])
        except KeyError:
            datarow.extend([0])
    datarow.extend([total])
    datalist.append(datarow)
    nullrow = [None]*len(datarow)
    datalist.append(nullrow)

    return datalist

def get_data_budget_provider(mytime, ids):
    """
    Return a csv containing provider budget and actuals by month.
    """
    months = {}
    data_points = defaultdict(dict)
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(mytime)
        providers = get_providers(ids.prv, dubconn)
        dubmetrics = get_data_general(mytime, ids, dubconn, group_by="prvid")
        for dubmetric in dubmetrics:
            months[dubmetric[0]] = 1
            data_points[providers[dubmetric[1]][0]][dubmetric[0]] = dubmetric[2]

        budgets, bgt_months = get_budget_provider_dict(ids, int(mytime.start),
                                                       int(mytime.end), dubconn)

        datalist = gen_cost_table(data_points, bgt_months, table_str='Actuals:')
        datalist += gen_cost_table(budgets, bgt_months, table_str='Budgets:')

        dubconn.close()

    return datalist


def get_budget_over_under(my_time, ids):
    """
    Return a csv containing provider actuals and budget over/under by month.
    Assumes a teamid is passed in the ids structure.
    """
    data_points = defaultdict(dict)
    datalist = []
    dubs = []
    providers = {}
    teams = {}

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        providers = get_providers(ids.prv, dubconn)
        teams = get_teams(ids.team, dubconn)
        if ids.team is not None:
            tmp_id = ids
            for teamval in ids.team:
                tmp_id.team = [teamval]
                data_points = defaultdict(dict)
                dubs = get_data_general(mytime, tmp_id, dubconn,
                                        group_by="prvid")
                for dub in dubs:
                    data_points[providers[dub[1]][0]][dub[0]] = dub[2]
                datalist += gen_over_under_table(data_points, tmp_id,
                                                 mytime, dubconn,
                                                 teams[int(teamval)] + ":")

        else:
            dubs = get_data_general(mytime, ids, dubconn,
                                    group_by="prvid")

            for dub in dubs:
                data_points[providers[dub[1]][0]][dub[0]] = dub[2]

            datalist = gen_over_under_table(data_points, ids, mytime,
                                            dubconn, table_str='All Teams:')

        dubconn.close()

    return datalist


def get_data_budget_team(my_time, ids):
    """
    Return a csv containing team budget and actuals by month.
    """
    months = {}
    data_points = defaultdict(dict)
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        teams = get_teams(ids.team, dubconn)
        dubmetrics = get_data_general(mytime, ids, dubconn, group_by="teamid")
        for dubmetric in dubmetrics:
            months[dubmetric[0]] = 1
            data_points[teams[dubmetric[1]]][dubmetric[0]] = dubmetric[2]


        budgets, bgt_months = get_budget_team_dict(ids, int(mytime.start),
                                                   int(mytime.end), dubconn)
        datalist = gen_cost_table(data_points, bgt_months, table_str='Actuals:')
        datalist += gen_cost_table(budgets, bgt_months, table_str='Budgets:')

        dubconn.close()

    return datalist

def get_data_budget_div(my_time, ids):
    """
    Return a csv containing division budget and actuals by month.
    """
    months = {}
    dubmetrics = defaultdict(lambda: defaultdict(int))
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        divs = get_divisions(ids.div, dubconn)
        ids = set_teams_from_divs(ids, dubconn)
        t_divs = lookup_divisions(ids.team, dubconn)
        t_metrics = get_data_general(mytime, ids, dubconn, group_by="teamid")
        for t_met in t_metrics:
            dubmetrics[divs[t_divs[t_met[1]]]][t_met[0]] += t_met[2]
            months[t_met[0]] = 1

        budgets, bgt_months = get_budget_div_dict(ids, mytime, divs,
                                                  t_divs, dubconn)
        datalist = gen_cost_table(dubmetrics, bgt_months, table_str='Actuals:')
        datalist += gen_cost_table(budgets, bgt_months, table_str='Budgets:')

        dubconn.close()

    return datalist


def get_data_item_cost(my_time, ids):
    """
    Return a csv containing item costs by project, provider, team.
    """
    datalist = []
    query_params = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        # retrieve raw list of rows, one per actual/budget

        query = """
                   SELECT DATE_FORMAT(md.datetime,%s), mt.metricname,
                   CAST(IFNULL(sum(md.cost),0) AS SIGNED INT), prj.extname,
                   prv.prvname, tm.teamname FROM metricdata AS md 
                   JOIN teams AS tm ON md.teamid = tm.teamid
                   JOIN metrictypes AS mt ON md.metric = mt.metricid
                   JOIN projects AS prj ON md.prjid = prj.prjid
                   JOIN providers AS prv ON md.prvid = prv.prvid
                   WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                   FROM_UNIXTIME(%s) """
        query_params.append(mytime.dformat)
        query_params.append(mytime.start)
        query_params.append(mytime.end)
        if ids.team is not None:
            myformat = ','.join(['%s'] * len(ids.team)) + ')'
            query += " AND md.teamid IN ("
            query += myformat
            for teamval in ids.team:
                query_params.append(int(teamval))
        if ids.project is not None:
            query += " AND md.prjid = %s "
            query_params.append(int(ids.project))
        if ids.prv is not None:
            myformat = ','.join(['%s'] * len(ids.prv)) + ')'
            query += " AND md.prvid IN ("
            query += myformat
            for prv_val in ids.prv:
                query_params.append(int(prv_val))
        query += " GROUP by DATE_FORMAT(md.datetime,%s), md.metric "
        query += " ORDER BY md.teamid, md.prvid, md.prjid, md.metric, "
        query += " DATE_FORMAT(md.datetime,%s)"
        query_params.append(mytime.dformat)
        query_params.append(mytime.dformat)

        dubmetrics = utils.get_from_db(query, query_params, dubconn)
        header = ['Date', 'Item', 'Cost', 'Project', 'Provider', 'Team']
        datalist = gen_item_table(dubmetrics, header, inc_total=True,
                                  sum_col=2)

        dubconn.close()

    return datalist


def get_data_general(my_time, ids, dubconn, group_by):
    """
    Make the DB call for the given budget actuals.
    """
    query_params = []

    query = " SELECT DATE_FORMAT(datetime,%s), " + group_by
    query += """,  CAST(IFNULL(sum(cost),0) AS SIGNED INT) FROM metricdata
                WHERE datetime BETWEEN FROM_UNIXTIME(%s) AND
                FROM_UNIXTIME(%s) """
    query_params.append(my_time.dformat)
    query_params.append(my_time.start)
    query_params.append(my_time.end)
    if ids.team is not None:
        myformat = ','.join(['%s'] * len(ids.team)) + ')'
        query += " AND teamid IN ("
        query += myformat
        for teamval in ids.team:
            query_params.append(int(teamval))
    if ids.project is not None:
        query += " AND prjid = %s "
        query_params.append(int(ids.project))
    if ids.prv is not None:
        myformat = ','.join(['%s'] * len(ids.prv)) + ')'
        query += " AND prvid IN ("
        query += myformat
        for prv_val in ids.prv:
            query_params.append(int(prv_val))
    query += " GROUP BY " + group_by
    query += " , DATE_FORMAT(datetime,%s)"
    query_params.append(my_time.dformat)
    return utils.get_from_db(query, query_params, dubconn)

def get_data_provider(my_time, ids, add_budget):
    """
    Return dubweb values for each provider, by given time period.
    """
    providers = {}
    months = {}
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        providers = get_providers(ids.prv, dubconn)
        dubmetrics = get_data_general(mytime, ids, dubconn, group_by="prvid")

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[2] is not None:
                data_point = {}
                data_point["Month"] = dubmetric[0]
                data_point["Provider"] = providers[dubmetric[1]][0]
                data_point["Spend"] = dubmetric[2]
                datalist.append(data_point)
                months[dubmetric[0]] = 1

        if add_budget:
            datalist = add_budget_series_providers(ids, months, datalist,
                                                   providers, dubconn)

        dubconn.close()
    return json.dumps(datalist)

def get_data_team(my_time, ids, add_budget):
    """
    Return dubweb values for each team, by given time period.
    """
    teams = {}
    months = {}
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        teams = get_teams(ids.team, dubconn)
        dubmetrics = get_data_general(mytime, ids, dubconn, group_by="teamid")

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[2] is not None:
                data_point = {}
                data_point["Month"] = dubmetric[0]
                data_point["Team"] = teams[dubmetric[1]]
                data_point["Spend"] = dubmetric[2]
                datalist.append(data_point)
                months[dubmetric[0]] = 1

        if add_budget:
            datalist = add_budget_series_teams(ids, months, datalist,
                                               teams, dubconn)


        dubconn.close()
    return json.dumps(datalist)

def get_data_div(my_time, ids, add_budget):
    """
    Return dubweb values for each division, by given time period.
    """
    divisions = {}
    dubmetrics = defaultdict(lambda: defaultdict(int))
    months = {}
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        divisions = get_divisions(ids.div, dubconn)
        ids = set_teams_from_divs(ids, dubconn)
        team_divs = lookup_divisions(ids.team, dubconn)
        t_metrics = get_data_general(mytime, ids, dubconn, group_by="teamid")
        for t_metric in t_metrics:
            if len(t_metric) > 0 and t_metric[2] is not None:
                # sum across divisions
                dubmetrics[team_divs[t_metric[1]]][t_metric[0]] += t_metric[2]

        for div in dubmetrics:
            for month in dubmetrics[div]:
                if dubmetrics[div][month] > 0:
                    data_point = {}
                    data_point["Month"] = month
                    data_point["Division"] = divisions[div]
                    data_point["Spend"] = dubmetrics[div][month]
                    datalist.append(data_point)
                    months[month] = 1

        if add_budget:
            datalist = add_budget_series_divisions(ids, months, datalist,
                                                   divisions, team_divs,
                                                   dubconn)


        dubconn.close()
    return json.dumps(datalist)

def get_data_project(my_time, ids, add_budget):
    """
    Return dubweb values for each project, by given time period.
    """
    projects = {}
    months = {}
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        mytime = get_date_filters(my_time)
        projects = get_projects(ids.prv, ids.team, ids.project, dubconn)
        dubmetrics = get_data_general(mytime, ids, dubconn, group_by="prjid")

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
    Return dubweb values for each workload, by given time period.
    Note: Workload is restricted to one provider and project.
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
        ids.prv = ids.prv[0]
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
        query_params.append(int(ids.prv))
        query_params.append(int(ids.project))
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
            myformat = ','.join(['%s'] * len(ids.team)) + ')'
            query += " AND teamid IN ("
            query += myformat
            for teamval in ids.team:
                query_params.append(int(teamval))
        if ids.project is not None:
            query += " AND prjid = %s "
            query_params.append(int(ids.project))
        if ids.prv is not None:
            myformat = ','.join(['%s'] * len(ids.prv)) + ')'
            query += " AND prvid IN ("
            query += myformat
            for prv_val in ids.prv:
                query_params.append(int(prv_val))
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
            datalist = add_budget_series_providers(ids, months, datalist,
                                                   providers, dubconn)


        dubconn.close()
    return json.dumps(datalist)

def estimate_data_team(mytime, ids, add_budget):
    """
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
            myformat = ','.join(['%s'] * len(ids.team)) + ')'
            query += " AND teamid IN ("
            query += myformat
            for teamval in ids.team:
                query_params.append(int(teamval))
        if ids.project is not None:
            query += " AND prjid = %s "
            query_params.append(int(ids.project))
        if ids.prv is not None:
            myformat = ','.join(['%s'] * len(ids.prv)) + ')'
            query += " AND prvid IN ("
            query += myformat
            for prv_val in ids.prv:
                query_params.append(int(prv_val))
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
            datalist = add_budget_series_teams(ids, months, datalist,
                                               teams, dubconn)

        dubconn.close()
    return json.dumps(datalist)

