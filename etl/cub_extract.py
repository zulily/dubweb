#!/usr/bin/python
"""
    This script will extract metrics from a source, based on the rules
    contained in the driver file, in the zu subdirectory.  Optionally,
    add -d to the command line in order to debug (no MySQLDB metric writes).
    Add -v to the command line for verbose output from imported modules.

    python cub_extract.py -d -f ./zu/zu_advanced_meta.json

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

import calendar
import MySQLdb
import os
import sys
import json
import argparse
import glob
import re
import csv
import logging
import pprint
from dateutil import parser
from collections import defaultdict

class DUBLoad(object):
    """
        Class for each metric set (e.g., a day of datacenter foo's metrics,
        or a month of datacenter bar's metrics).  Includes separate instance
        of projects teams, as each set can add projects.
    """

    def __init__(self, prv_def, prv_id, metric_date, metrics,
                 metric_defs, conn):
        """
        Initialize the object, processing the data for the file
        """

        self.current_stats = []
        self._prvid = prv_id
        self._conn = conn
        self._metric_date = metric_date
        self._metric_format = prv_def[3]
        self._timeunit = prv_def[4]
        self._delimiter = prv_def[5]
        self._metric_types = self._get_metric_types()
        self._projects = self._get_projects_for_provider()
        self._teams = self._get_teams()

        if self._metric_format == "json":
            self._parse_billing_json(metrics, metric_defs["permetric"])
        elif self._metric_format == "csv":
            self._parse_billing_csv(metrics, metric_defs["permetric"])

        if 'various' in metric_defs:
            taxrate = self._get_provider_taxrate()
            self._post_process_stats(taxrate, metric_defs['various'])

    def _parse_billing_json(self, my_metrics, metric_evals):
        """
        Given a set of billing metrics, calculate the final (per day)
        metrics for the given metrics provider.
        """

        for metric in my_metrics:
            result_array = []
            for metric_eval in metric_evals:
                try:
                    value = eval(metric_eval)
                except KeyError:
                    #support has no projectNumber
                    value = "0"
                result_array.append(value)
            if result_array[1] not in self._projects:
                # add a new team (can delete later if necessary)
                # add the new project under the new team
                self._teams = self._add_team('unk')
                last_team_id = sorted(self._teams.keys())[-1]
                self._projects = self._add_project('unk',
                                                   result_array[1],
                                                   last_team_id)
            if result_array[2] not in self._metric_types:
                self._metric_types = self._add_metric_type(result_array[2],
                                                           result_array[4])
            # get team id before remapping prjid
            result_array.append(self._projects[result_array[1]][1])
            # clean up prjid, etc.
            result_array[1] = self._projects[result_array[1]][0]
            result_array[2] = self._metric_types[result_array[2]][0]
            self.current_stats.append(result_array)

        # hourly data needs to be aggregated
        if self._timeunit == "hour":
            self.current_stats = self._aggregate_hourly_data()


    def _parse_billing_csv(self, csvmetrics, metric_evals):
        """
        Given a set of csv billing data,
        compute provider/team/project daily bill.
        """

        for metric in csvmetrics:
            result_array = []
            for metric_eval in metric_evals:
                try:
                    value = eval(metric_eval)
                except KeyError:
                    #support has no projectNumber
                    value = "0"
                result_array.append(value)
            if not result_array[0] or result_array[0].isalpha() or \
                   result_array[2] is self._delimiter:
                continue
            if result_array[1] not in self._projects:
                # add a new team (can delete later if necessary)
                # add the new project under the new team
                self._teams = self._add_team('unk')
                last_team_id = sorted(self._teams.keys())[-1]
                self._projects = self._add_project('unk',
                                                   result_array[1],
                                                   last_team_id)
            if result_array[2] not in self._metric_types:
                self._metric_types = self._add_metric_type(result_array[2],
                                                           result_array[4])
            # get team id before remapping prjid
            result_array.append(self._projects[result_array[1]][1])
            # clean up prjid, etc.
            result_array[1] = self._projects[result_array[1]][0]
            result_array[2] = self._metric_types[result_array[2]][0]

            #generate daily data if necessary
            if self._timeunit == "month":
                self._add_daily_data(result_array)
            else:
                self.current_stats.append(result_array)

        # hourly data needs to be aggregated
        if self._timeunit == "hour":
            self.current_stats = self._aggregate_hourly_data()


    def _add_daily_data(self, in_array):
        """
        Generate a month's worth of daily data (with modified cost/hours)
        """
        dateparts = self._metric_date.split('-')
        (startday, daycount) = calendar.monthrange(int(dateparts[0]),
                                                   int(dateparts[1]))
        cost = int(in_array[5]) / float(daycount)
        # add 1 to handle range's lack of inclusiveness on top value
        daycount += 1
        for i in range(1, daycount):
            thedate = dateparts[0] + '-' + dateparts[1] + '-' + str(i)
            thedate += 'T00:00:00'
            self.current_stats.append([thedate, in_array[1], in_array[2],
                                       86400, 'seconds', cost, in_array[6]])


    def _aggregate_hourly_data(self):
        """
        Aggregate hourly data for the previous day (modified cost/hours)
        """
        daily_stats = defaultdict(dict)
        for metric in self.current_stats:
            try:
                daily_stats[metric[2]][3] = \
                 float(daily_stats[metric[2]][3]) + float(metric[3])
                daily_stats[metric[2]][5] = \
                 float(daily_stats[metric[2]][5]) + float(metric[5])
            except KeyError:
                daily_stats[metric[2]] = metric
                daily_stats[metric[2]][0] = self._metric_date + 'T00:00:00'
        return daily_stats.values()


    def _post_process_stats(self, taxrate, summary_metrics):
        """
        Do any final calculations necessary.
        """
        for metric in summary_metrics:
            if metric[0].find("none") == -1:
                valuestring = metric[1]
                thedate = eval(valuestring)
                valuestring = metric[2]
                metricid = eval(valuestring)
                valuestring = metric[3]
                projectid = eval(valuestring)
                valuestring = metric[5]
                cost = eval(valuestring)
                valuestring = metric[6]
                teamid = eval(valuestring)
                self.current_stats.append([thedate, projectid, metricid,
                                           '86400', 'seconds', cost, teamid])


    def _get_teams(self):
        """
        Get teams from  MySQL cub DB
        """
        cursor = self._conn.cursor()
        teams = {}
        try:
            cursor.execute("SELECT teamid, teamname FROM teams")
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)

        output = cursor.fetchall()
        for i in range(0, len(output)):
            teams[output[i][0]] = output[i][1]

        cursor.close()
        return teams

    def _get_metric_types(self):
        """
        Get metrics types from  MySQL cub DB
        """
        cursor = self._conn.cursor()
        metrictypes = {}
        query = "SELECT metricname, metricid, unit FROM metrictypes \
                 WHERE prvid = %s"
        try:
            cursor.execute(query, (self._prvid))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)

        output = cursor.fetchall()
        for i in range(0, len(output)):
            metrictypes[output[i][0]] = [output[i][1], output[i][2]]

        cursor.close()
        return metrictypes

    def _add_metric_type(self, name, unit):
        """
        Add metrics type to  MySQL cub DB
        """
        cursor = self._conn.cursor()
        metrictypes = {}
        query = """\
        INSERT INTO metrictypes (metricname, unit, prvid) VALUES (%s,%s,%s)
        """
        try:
            cursor.execute(query, (name, unit, self._prvid))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)
        self._conn.commit()
        query = """\
        SELECT metricname, metricid, unit FROM metrictypes WHERE prvid = %s
        """
        try:
            cursor.execute(query, (self._prvid))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)

        output = cursor.fetchall()
        for i in range(0, len(output)):
            metrictypes[output[i][0]] = [output[i][1], output[i][2]]

        cursor.close()
        return metrictypes

    def _add_team(self, teamname):
        """
        Add team to  MySQL cub DB
        """
        cursor = self._conn.cursor()
        query = "INSERT INTO teams (teamname) VALUES (%s)"
        try:
            cursor.execute(query, (teamname))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)

        self._conn.commit()
        cursor.close()
        return self._get_teams()

    def _add_project(self, extname, extid, teamid):
        """
        Add project to  MySQL cub DB
        """
        cursor = self._conn.cursor()
        query = """\
        INSERT INTO projects (extname, extid, prvid, teamid) VALUES (%s,%s,%s,%s)
        """
        try:
            cursor.execute(query, (extname, extid, self._prvid, teamid))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)
        self._conn.commit()
        cursor.close()
        return self._get_projects_for_provider()

    def update_provider_stats(self, stats_date):
        """
        Update ETL time for provider in MySQL DB
        """
        cursor = self._conn.cursor()
        query = "UPDATE providers SET lastetl = %s WHERE prvid = %s"

        try:
            cursor.execute(query, (stats_date, self._prvid))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)
        self._conn.commit()
        cursor.close()

    def _get_provider_taxrate(self):
        """
        Get current provider taxrate from  MySQL DB
        """
        cursor = self._conn.cursor()
        query = "SELECT taxrate FROM providers WHERE prvid = %s"
        try:
            cursor.execute(query, (self._prvid))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)

        output = cursor.fetchall()
        cursor.close()
        return float(output[0][0])


    def _get_projects_for_provider(self):
        """
        Get projects provider id from  MySQL cub DB
        """
        cursor = self._conn.cursor()
        projects = {}
        query = """\
        SELECT extid, prjid, teamid FROM projects WHERE prvid = %s
        """

        try:
            cursor.execute(query, (self._prvid))
        except MySQLdb.Error, err:
            print "Error %d: %s" % (err.args[0], err.args[1])
            sys.exit(1)

        output = cursor.fetchall()
        for i in range(0, len(output)):
            projects[output[i][0]] = [output[i][1], output[i][2]]

        cursor.close()
        return projects

    def write_stats(self):
        """
        Write current_stats to the MySQL DB
        Truncate to UTC, as each provider bills according
        to their own time zone logic.
        """
        cursor = self._conn.cursor()
        query = """\
        INSERT INTO metricdata
        (datetime, metric, data, prjid, cost, prvid, teamid)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        for metric in self.current_stats:
            mytime = parser.parse(metric[0])
            trunctime = mytime.replace(second=0, microsecond=0)
            project = metric[1]
            metricid = metric[2]
            value = int(round(float(metric[3])))
            cost = int((float(metric[5])*100)+0.5) / 100.0
            team_id = metric[6]
            try:
                cursor.execute(query, (trunctime, metricid, value,
                                       project, cost, self._prvid, team_id))
            except MySQLdb.Error, err:
                print "Error %d: %s" % (err.args[0], err.args[1])
                sys.exit(1)

        self._conn.commit()
        cursor.close()


def load_json_file(filename):
    """
    Load definition file (json).
    """
    try:
        with open(filename, 'r') as historyfile:
            mydict = json.load(historyfile)
    except IOError:
        mydict = ""
        print " Couldn't load " + filename + "\n"
    return mydict

def load_csv_file(filename):
    """
    Load csv file (all).
    """
    with open(filename, 'r') as filehandle:
        #read csv into a list of lists
        data = list(list(rec) for rec in csv.reader(filehandle, delimiter=','))
    filehandle.close()
    return data

def open_monitoring_db(dbhost, dbuser, dbpass, database):
    """
    Open MySQL monitoring DB
    """
    try:
        conn = MySQLdb.connect(host=dbhost, user=dbuser,
                               passwd=dbpass, db=database)

    except MySQLdb.Error, err:
        print "Error %d: %s" % (err.args[0], err.args[1])
        sys.exit(1)

    return conn

def load_latest_metrics(conn, prefix, filetype, provider_id):
    """
    Load metrics generated since lastetl value in provider
    table of MySQL cub DB
    """
    stats = {}
    cursor = conn.cursor()

    query = "SELECT prv.lastetl FROM providers AS prv WHERE prv.prvid = %s"
    try:
        cursor.execute(query, (provider_id))
    except MySQLdb.Error, err:
        print "Error %d: %s" % (err.args[0], err.args[1])
        sys.exit(1)

    output = cursor.fetchall()
    if output[0][0]:
        lastetl = output[0][0]
    else:
        lastetl = parser.parse("1900-01-01 00:00:00")

    #find local files since lastetl
    localfiles = glob.glob(prefix + "*")
    datepattern = prefix + "(\d{4}-\d{2}-\d{2}).*"
    for currentfile in localfiles:
        datepart = re.search(datepattern, currentfile)
        curdatestring = datepart.group(1)
        curdate = parser.parse(curdatestring)
        if curdate > lastetl:
            if filetype == "json":
                stats[curdatestring] = load_json_file(currentfile)
            else:
                stats[curdatestring] = load_csv_file(currentfile)

    cursor.close()
    return stats


def get_provider_id(conn, provider):
    """
    Get current provider id from  MySQL cub DB
    """
    cursor = conn.cursor()
    query = "SELECT prvid FROM providers WHERE prvname = %s"
    try:
        cursor.execute(query, (provider))
    except MySQLdb.Error, err:
        print "Error %d: %s" % (err.args[0], err.args[1])
        sys.exit(1)

    output = cursor.fetchall()
    cursor.close()
    return int(output[0][0])

def parse_arguments():
    """
    Collect command-line arguments
    """
    my_parser = argparse.ArgumentParser(
                                        description='Extract metrics from Zabbix and load into perf db.')
    my_parser.add_argument('-f', dest='filename',
                           help='path to json file with metrics rules',
                           required=True)
    my_parser.add_argument('--verbose', '-v', dest='verbose',
                           action='store_true', help='enable verbose messages')
    my_parser.add_argument('--debug', '-d', dest='debug', action='store_true',
                           help='enable debug-only mode (no mysql writing)')
    return my_parser

def configure_logging(args):
    """
    Logging to console
    """
    format_string = '%(levelname)s:%(name)s:line %(lineno)s:%(message)s'
    log_format = logging.Formatter(format_string)
    log_level = logging.INFO if args.verbose else logging.WARN
    log_level = logging.DEBUG if args.debug else log_level
    console = logging.StreamHandler()
    console.setFormatter(log_format)
    console.setLevel(log_level)
    root_logger = logging.getLogger()
    if len(root_logger.handlers) == 0:
        root_logger.addHandler(console)
    root_logger.setLevel(log_level)
    root_logger.handlers[0].setFormatter(log_format)
    return logging.getLogger(__name__)


# Main functionality

def main():
    """
    Main function for metrics processing, may generate
    many months of data in one run
    """
    args = parse_arguments().parse_args()
    logger = configure_logging(args)

    # Change to metrics directory containing definition file
    os.chdir(os.path.dirname(args.filename))
    filename = os.path.basename(args.filename)

    defs = defaultdict(list)
    defs = load_json_file(filename)

    if logger.isEnabledFor(logging.DEBUG):
        logging.debug('Got filename of %s', filename)
        logging.debug(pprint.pformat(defs))

    # open metrics DB
    conn = open_monitoring_db(defs["dbhost"], defs["dbuser"],
                              defs["dbpass"], defs["database"])

    # Iterate through providers, loading their stats files
    for prvdef in defs["metricstypes"]:
        provider = prvdef[0]
        provider_id = get_provider_id(conn, provider)
        if provider_id < 1:
            #unknown provider
            continue
        statsfilename = prvdef[1]
        prvmetricdefs = load_json_file(statsfilename)
        if logger.isEnabledFor(logging.DEBUG):
            logging.debug('Got provider of %s', provider)
            logging.debug('Got stats file of %s', statsfilename)
            logging.debug(pprint.pformat(prvmetricdefs))

        # load latest given metric files for a provider
        providermetrics = load_latest_metrics(conn, prvdef[2], prvdef[3],
                                              provider_id)
        if not providermetrics:
            logging.debug('No metrics found for %s', provider)
            continue
        metricdates = sorted(providermetrics.iterkeys())
        logging.debug('Got a last metrics date of %s', metricdates[-1])

        # Create a DubLoad instance for each day/month of metrics
        for metricrun in metricdates:
            dub_load = DUBLoad(prvdef, provider_id, metricrun,
                               providermetrics[metricrun], prvmetricdefs, conn)
            if logger.isEnabledFor(logging.DEBUG):
                logging.debug('On %s, %s gave current_stats of',
                              metricrun, provider)
                logging.debug(pprint.pformat(dub_load.current_stats))
            elif len(dub_load.current_stats) > 0:
                dub_load.write_stats()
                #todo if not success, then handle it here
                dub_load.update_provider_stats(metricrun)

    # end provider loop
    conn.close()



if __name__ == '__main__':
    sys.exit(main())
