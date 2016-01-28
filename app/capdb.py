#!/usr/bin/env python
"""
cap helper library
   Called by flask cap app
   to pull cap data, etc.

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

import datetime
import json
from collections import OrderedDict
from dateutil import parser

from app import app
import app.utils as utils

#globals
SETTINGS_FILE = "/var/dubweb/.cap_settings"

def get_cap_ids(cap_ids, cap_conn):
    """
    Given capacity metric id or None
    Return a dictionary of capacity metrics where you have name,
    id, metricid, and lastetl  for the given (or all) capmetric(s)
    """

    capdict = {}
    query = """
            SELECT typeid, typename, metricid, lastetl FROM capacity_types 
            """
    cursor = cap_conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            if cap_ids is None or str(row[0]) in cap_ids:
                capdict[str(row[0])] = [row[0], row[1], row[2], row[3]]
    except Exception, err:
        app.logger.error("mysql exception: %s", err.message)
        app.logger.error("from query: %s", query)
    finally:
        cursor.close()

    return capdict


def get_capacity_limits(ids, cap_conn):
    """
    TODO:
    Given a set of capacity metric ids,
    Return cap limit values.
    """

    query_params = []
    data_list = []
    query = "SELECT id, CAST(IFNULL(limit),0) AS SIGNED INT)"
    query += " FROM capacity_limits WHERE id = %s"

    limit_list = utils.get_from_db(query, tuple(query_params), cap_conn)
    for limit in limit_list:
        data_point = {}
        data_list.append(data_point)

    return data_list


def get_capacity_daily(ids, add_limits):
    """
    Given a list of capacity metric ids, and optional flags
    for adding the limit per component,
    Return capacity estimates for the given metrics' period.
    """
    datalist = []
    query_params = []
    capmetrics = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, capconn = utils.open_monitoring_db(settings['cdbhost'],
                                                settings['cdbuser'],
                                                settings['cdbpass'],
                                                settings['cdb_db'])

    if success:
        cap_ids = get_cap_ids(ids, capconn)
        for capkey in cap_ids.iterkeys():
            query = """SELECT period, typeid, value FROM capacity_estimates
                   WHERE typeid = (%s)  ORDER by typeid, period ASC"""
            query_params = [capkey]
            capmetrics += utils.get_from_db(query, query_params, capconn)

        for capmetric in capmetrics:
            if len(capmetric) > 0 and capmetric[2] is not None:
                data_point = {}
                data_point["Period"] = capmetric[0]
                data_point["Metric"] = cap_ids[str(capmetric[1])][1]
                data_point["Value"] = capmetric[2]
                datalist.append(data_point)

        if add_limits:
            datalist = get_capacity_limits(ids, capconn)

        capconn.close()
    return json.dumps(datalist)

def get_cap_coefs(my_id, conn):
    """
    Get current capacity coefficients from MySQL capacity DB
    """
    coefs = {}
    query = """
               SELECT constname, constval FROM capacity_constants
               WHERE typeid = %s
            """
    query_params = [my_id]
    output = utils.get_from_db(query, query_params, conn)

    for i in range(0, len(output)):
        coefs[output[i][0]] = output[i][1]
    return coefs


def get_cap_model_metrics(my_id, conn):
    """
    Get current capacity model from MySQL capacity DB
    """
    metrics = OrderedDict()
    query = """
               SELECT period, factor FROM capacity_patterns
               WHERE typeid = %s
               ORDER BY period ASC
            """
    query_params = [my_id]
    output = utils.get_from_db(query, query_params, conn)
    for i in range(0, len(output)):
        metrics[output[i][0]] = output[i][1]
    return metrics


def get_capacity_model(ids):
    """
    Given a list of capacity metric ids,
    Return capacity model and coefficient for the given metric.
    """
    capmodels = {}

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, capconn = utils.open_monitoring_db(settings['cdbhost'],
                                                settings['cdbuser'],
                                                settings['cdbpass'],
                                                settings['cdb_db'])

    if success:
        cap_ids = get_cap_ids(ids, capconn)
        for capkey in cap_ids.iterkeys():
            capmodels[capkey] = {}
            capmodels[capkey]['coef'] = get_cap_coefs(capkey, capconn)
            capmodels[capkey]['model'] = get_cap_model_metrics(capkey,
                                                               capconn)

        capconn.close()
    return json.dumps(capmodels)

def get_driver_metric(source_metric, my_date):
    """
    Get external perfdata metric that drives capacity.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    msuccess, monconn = utils.open_monitoring_db(settings['mdbhost'],
                                                 settings['mdbuser'],
                                                 settings['mdbpass'],
                                                 settings['mdb_db'])

    if msuccess:
        cursor = monconn.cursor()

        query = """
                SELECT CAST(max(pd.data) AS SIGNED) AS metric_total
                FROM perfdata pd
                JOIN perftypes pt ON pt.metricid = pd.metric
                WHERE pt.metricname = %s
               """
        try:
            cursor.execute(query, (source_metric[0], my_date))
            drivermetric = cursor.fetchall()

        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])

        cursor.close()
        monconn.close()
    return drivermetric[0][0]


def get_monitor_daily(ids, opt_date):
    """
    Given a list of capacity metric ids, and an optional flag
    for returning a different date,
    Return capacity estimates for the given metrics' period.
    """
    datalist = []
    query_params = []
    monmetrics = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    csuccess, capconn = utils.open_monitoring_db(settings['cdbhost'],
                                                 settings['cdbuser'],
                                                 settings['cdbpass'],
                                                 settings['cdb_db'])
    msuccess, monconn = utils.open_monitoring_db(settings['mdbhost'],
                                                 settings['mdbuser'],
                                                 settings['mdbpass'],
                                                 settings['mdb_db'])

    if csuccess and msuccess:
        if opt_date is None:
            now = datetime.datetime.now()
        else:
            now = parser.parse(opt_date)
        opt_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cap_ids = get_cap_ids(ids, capconn)
        for capkey in cap_ids.iterkeys():
            query = """SELECT DATE_FORMAT(datetime,'%%H:%%i'),  data,
                       %s as ID
                       FROM perfdata WHERE metric = %s AND 
                       datetime BETWEEN %s AND
                       DATE_ADD(%s, INTERVAL '23:59:59' HOUR_SECOND)
                       ORDER by datetime ASC"""
            query_params = [capkey, cap_ids[capkey][2], opt_date, opt_date]
            monmetrics += utils.get_from_db(query, query_params, monconn)

        for monmetric in monmetrics:
            metname = cap_ids[str(monmetric[2])][1] +"_act"
            if len(monmetric) > 0 and monmetric[1] is not None:
                data_point = {}
                data_point["Period"] = monmetric[0]
                data_point["Metric"] = metname
                data_point["Value"] = monmetric[1]
                datalist.append(data_point)

        monconn.close()
        capconn.close()
    return json.dumps(datalist)

