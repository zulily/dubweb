#!/usr/bin/env python
"""
admindb helper library
   Called by flask app admin
   to modify budgets, etc.

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

#globals
SETTINGS_FILE = "/var/dubweb/.admin_settings"

class AdmIDs(object):
    """
    admindb ids helper class
    """
    def __init__(self, prv_id, team_id, project_id, budget_id):
        """
        Initial ids for chart
        """
        self.prv = prv_id
        self.team = team_id
        self.project = project_id
        self.budget = budget_id

def format_budget(bgt_id, bgt, month, comment, team_id, prv_id):
    """
    Helper for budget row formatting
    """
    data_point = {}
    data_point["ID"] = bgt_id
    data_point["Budget"] = bgt
    data_point["Month"] = month
    data_point["Comment"] = comment
    data_point["TeamID"] = team_id
    data_point["ProviderID"] = prv_id
    return data_point

def format_provider(prv_id, name, lastetl, taxrate):
    """
    Helper for provider row formatting
    """
    data_point = {}
    data_point["ID"] = prv_id
    data_point["Name"] = name
    data_point["LastETL"] = lastetl
    data_point["TaxRate"] = taxrate
    return data_point

def format_team(team_id, name):
    """
    Helper for team row formatting
    """
    data_point = {}
    data_point["ID"] = team_id
    data_point["Name"] = name
    return data_point

def format_project(prj_id, name, extid, team_id, prv_id):
    """
    Helper for project row formatting
    """
    data_point = {}
    data_point["ID"] = prj_id
    data_point["ExtName"] = name
    data_point["ExtID"] = extid
    data_point["TeamID"] = team_id
    data_point["ProviderID"] = prv_id
    return data_point

def get_budget_items(ids, m_filter, bgt_filter):
    """
    Given a time, and optional filters for provider, team, month,
    budget...
    Return list of budget entries.
    """
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        params = []
        query = """
                    SELECT distinct budgetid, budget, month,
                    IFNULL(comment,""), teamid, prvid
                    FROM budgetdata WHERE 1 """
        if ids.team is not None:
            query += " AND teamid = %s "
            params.append(str(ids.team))
        if ids.budget is not None:
            query += " AND budgetid = %s "
            params.append(str(ids.budget))
        if ids.prv is not None:
            query += " AND prvid = %s "
            params.append(str(ids.prv))
        if m_filter is not None:
            query += " AND month LIKE %s "
            params.append(m_filter + "%")
        if bgt_filter is not None:
            query += " AND budget LIKE %s "
            params.append(str(bgt_filter) + "%")

        app.logger.debug("get budget query: %s", query)

        dubmetrics = utils.get_from_db(query, tuple(params), dubconn)

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[1] is not None:
                budget_row = format_budget(bgt_id=dubmetric[0],
                                           bgt=dubmetric[1],
                                           month=dubmetric[2],
                                           comment=dubmetric[3],
                                           team_id=dubmetric[4],
                                           prv_id=dubmetric[5])
                datalist.append(budget_row)


        dubconn.close()
    return datalist

def edit_budget_item(ids, my_month, my_budget, my_comment):
    """
    Given budget id, and modified: providers, team, project,
    budget, or month
    Return modified budget entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        budget = format_budget(bgt_id=int(ids.budget),
                               bgt=int(my_budget),
                               month=my_month,
                               comment=my_comment,
                               team_id=int(ids.team),
                               prv_id=int(ids.prv))

        query = """
                    UPDATE budgetdata
                    SET budget=%s, month=%s, teamid=%s, prvid=%s, comment=%s
                    WHERE budgetid=%s
                """
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (budget['Budget'], budget['Month'],
                                   budget['TeamID'], budget['ProviderID'],
                                   budget['Comment'], budget['ID']))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return budget

def insert_budget_item(ids, my_month, my_budget, my_comment):
    """
    Given providers, team, project, budget, and month
    Return inserted budget entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        budget = format_budget(bgt_id=None,
                               bgt=int(my_budget),
                               month=my_month,
                               comment=my_comment,
                               team_id=int(ids.team),
                               prv_id=int(ids.prv))

        query = """
                    INSERT INTO budgetdata
                    (budget, month, teamid, prvid, comment)
                    VALUES (%s, %s, %s, %s, %s)
                """
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (budget['Budget'], budget['Month'],
                                   budget['TeamID'], budget['ProviderID'],
                                   budget['Comment']))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return get_budget_items(ids, my_month, my_budget)[0]

def clone_budget_month(ids, src_month, dst_month):
    """
    Clone budget from source month into (empty) destination months.
    Return destination month budgets.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        my_comment = "Cloned from " + src_month
        query = """
                    INSERT IGNORE INTO budgetdata
                    (budget, month, teamid, prvid, comment)
                    VALUES (%s, %s, %s, %s, %s)
                """
        cursor = dubconn.cursor()
        src_budgets = get_budget_items(ids, m_filter=src_month,
                                       bgt_filter=None)
        for bdgt in src_budgets:
            budget = format_budget(bgt_id=None,
                                   bgt=int(bdgt['Budget']),
                                   month=dst_month,
                                   comment=my_comment,
                                   team_id=int(bdgt['TeamID']),
                                   prv_id=int(bdgt['ProviderID']))

            try:
                cursor.execute(query, (budget['Budget'], budget['Month'],
                                       budget['TeamID'], budget['ProviderID'],
                                       budget['Comment']))
            except Exception, err:
                app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                                 err.args[1])
                app.logger.error("generated by: %s", query)
                success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return get_budget_items(ids, m_filter=dst_month, bgt_filter=None)

def delete_budget_item(ids, my_month, my_budget, my_comment):
    """
    Given budget id, delete from db
    Return deleted budget entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        budget = get_budget_items(ids, my_month, my_budget)

        query = """
                    DELETE FROM budgetdata
                    WHERE budgetid=%s
                """
        app.logger.debug("Got a delete query of: %s ", query)
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (ids.budget,))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return budget[0]

def get_providers_admin(ids):
    """
    Given an optional filter for provider id (of a datacenter instance),
    Return list of provider details.
    """
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        params = []
        query = """
                    SELECT distinct prvid, prvname, lastetl, taxrate
                    FROM providers WHERE 1 """
        if ids.prv is not None:
            query += " AND prvid = %s "
            params.append(str(ids.prv))

        app.logger.debug("get provider query: %s", query)

        dubmetrics = utils.get_from_db(query, tuple(params), dubconn)

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[1] is not None:
                provider_row = format_provider(prv_id=dubmetric[0],
                                               name=dubmetric[1],
                                               lastetl=str(dubmetric[2]),
                                               taxrate=dubmetric[3])
                datalist.append(provider_row)


        dubconn.close()
    return datalist

def get_team_items(ids, name_filter):
    """
    Given optional filters for team id and name
    Return list of team entries.
    """
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        params = []
        query = """
                    SELECT distinct teamid, teamname
                    FROM teams WHERE 1 """
        if ids.team is not None:
            query += " AND teamid = %s "
            params.append(str(ids.team))
        if name_filter is not None:
            query += " AND teamname LIKE %s "
            params.append(name_filter + "%")

        app.logger.debug("get team query: %s", query)

        dubmetrics = utils.get_from_db(query, tuple(params), dubconn)

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[1] is not None:
                team_row = format_team(team_id=dubmetric[0],
                                       name=dubmetric[1])
                datalist.append(team_row)


        dubconn.close()
    return datalist

def edit_team_item(ids, my_teamname):
    """
    Given team id, and modified teamname
    Return modified team entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        team = format_team(team_id=int(ids.team), name=my_teamname)

        query = """
                    UPDATE teams
                    SET teamname=%s WHERE teamid=%s
                """
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (team['Name'], team['ID']))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return team

def insert_team_item(ids, my_teamname):
    """
    Given providers, team, project, team, and month
    Return inserted team entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        query = """
                    INSERT INTO teams
                    (teamname)
                    VALUES (%s)
                """
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (my_teamname,))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return get_team_items(ids, my_teamname)[0]

def delete_team_item(ids, my_teamname):
    """
    Given team id, delete from db
    Return deleted team entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        team = format_team(team_id=int(ids.team),
                           name=my_teamname)

        query = """
                    DELETE FROM teams
                    WHERE teamid=%s
                """
        app.logger.debug("Got a delete query of: %s ", query)
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (team['ID'],))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return team

def get_project_items(ids, name_filter, extid_filter):
    """
    Given optional filters for provider id, team id, project id,
    project name, project external id,...
    Return list of project entries.
    """
    datalist = []

    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        params = []
        query = """
                    SELECT distinct prjid, extname, extid,
                    prvid, teamid
                    FROM projects WHERE 1 """
        if ids.project is not None:
            query += " AND prjid = %s "
            params.append(str(ids.project))
        if ids.team is not None:
            query += " AND teamid = %s "
            params.append(str(ids.team))
        if ids.prv is not None:
            query += " AND prvid = %s "
            params.append(str(ids.prv))
        if name_filter is not None:
            query += " AND extname LIKE %s "
            params.append(name_filter + "%")
        if extid_filter is not None:
            query += " AND extid LIKE %s "
            params.append(str(extid_filter) + "%")

        app.logger.debug("get project query: %s", query)

        dubmetrics = utils.get_from_db(query, tuple(params), dubconn)

        for dubmetric in dubmetrics:
            if len(dubmetric) > 0 and dubmetric[1] is not None:
                project_row = format_project(prj_id=dubmetric[0],
                                             name=dubmetric[1],
                                             extid=dubmetric[2],
                                             prv_id=dubmetric[3],
                                             team_id=dubmetric[4])
                datalist.append(project_row)


        dubconn.close()
    return datalist

def edit_project_item(ids, my_extname, my_extid):
    """
    Given project id, and modified: providers, team, external name,
    or external id,
    Return modified project entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        project = format_project(prj_id=int(ids.project),
                                 name=my_extname,
                                 extid=my_extid,
                                 team_id=int(ids.team),
                                 prv_id=int(ids.prv))

        query = """
                    UPDATE projects
                    SET extname=%s, extid=%s, prvid=%s, teamid=%s
                    WHERE prjid=%s
                """
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (project['ExtName'], project['ExtID'],
                                   project['ProviderID'], project['TeamID'],
                                   project['ID']))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return project

def insert_project_item(ids, my_extname, my_extid):
    """
    Given providers, team, project, extname, and extid
    Return inserted project entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        project = format_project(prj_id=None,
                                 name=my_extname,
                                 extid=my_extid,
                                 team_id=int(ids.team),
                                 prv_id=int(ids.prv))

        query = """
                    INSERT INTO projects
                    (extname, extid, prvid, teamid)
                    VALUES (%s, %s, %s, %s)
                """
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (project['ExtName'], project['ExtID'],
                                   project['ProviderID'], project['TeamID']))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return get_project_items(ids, my_extname, my_extid)[0]

def delete_project_item(ids, my_extname, my_extid):
    """
    Given project id, delete from db
    Return deleted project entry.
    """
    settings = utils.load_json_definition_file(SETTINGS_FILE)
    success, dubconn = utils.open_monitoring_db(settings['dbhost'],
                                                settings['dbuser'],
                                                settings['dbpass'],
                                                settings['db_db'])

    if success:
        project = format_project(prj_id=int(ids.project),
                                 name=my_extname,
                                 extid=my_extid,
                                 team_id=int(ids.team),
                                 prv_id=int(ids.prv))

        query = """
                    DELETE FROM projects
                    WHERE prjid=%s
                """
        app.logger.debug("Got a delete query of: %s ", query)
        cursor = dubconn.cursor()
        try:
            cursor.execute(query, (project['ID'],))
        except Exception, err:
            app.logger.error("mysql exception: [%d]:  %s", err.args[0],
                             err.args[1])
            app.logger.error("generated by: %s", query)
            success = 0
        dubconn.commit()
        cursor.close()
        dubconn.close()
    return project

