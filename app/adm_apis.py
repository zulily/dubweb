"""
    flask handler for all admin API/data requests for dubweb
"""
from app import app
from flask import request
import json
import app.admindb as admindb

# Define all admin APIs
@app.route('/data/budgets/list', methods=['GET'])
def admin_budgets_get():
    """ API for listing/filtering budgets """
    prv_id = clean_jsgrid_int(request.args.get('ProviderID'))
    team_id = clean_jsgrid_int(request.args.get('TeamID'))
    prjid = None
    bgt_id = clean_jsgrid_int(request.args.get('ID'))
    budget_filter = clean_jsgrid_int(request.args.get('Budget'))

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    if request.args.get('Month') != "":
        month_filter = request.args.get('Month')
    else:
        month_filter = None
    return json.dumps(admindb.get_budget_items(myids, month_filter,
                      budget_filter))

@app.route('/data/budgets/edit', methods=['POST'])
def admin_budget_edit():
    """ API for editing a budget """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = None
    bgt_id = clean_jsgrid_int(request.form['ID'])

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    month = request.form['Month']
    budget = request.form['Budget']
    comment = request.form['Comment']

    return json.dumps(admindb.edit_budget_item(myids, month,
                              budget, comment))

@app.route('/data/budgets/insert', methods=['POST'])
def admin_budget_insert():
    """ API for inserting a budget """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    month = request.form['Month']
    budget = request.form['Budget']
    comment = request.form['Comment']

    return json.dumps(admindb.insert_budget_item(myids, month,
                              budget, comment))

@app.route('/data/budgets/delete', methods=['DELETE'])
def admin_budget_delete():
    """ API for deleting a budget """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = None
    bgt_id = clean_jsgrid_int(request.form['ID'])

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    month = request.form['Month']
    budget = request.form['Budget']
    comment = request.form['Comment']

    return json.dumps(admindb.delete_budget_item(myids, month,
                              budget, comment))

@app.route('/data/providers/list', methods=['GET'])
def admin_providers_get():
    """ API for listing providers """
    prv_id = clean_jsgrid_int(request.args.get('ID'))
    team_id = None
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    return json.dumps(admindb.get_providers_admin(myids))

@app.route('/data/teams/list', methods=['GET'])
def admin_teams_get():
    """ API for listing/filtering teams """
    team_id = clean_jsgrid_int(request.args.get('ID'))
    prv_id = None
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    if request.args.get('Name') != "":
        my_name_filter = request.args.get('Name')
    else:
        my_name_filter = None
    return json.dumps(admindb.get_team_items(myids, my_name_filter))

@app.route('/data/teams/edit', methods=['POST'])
def admin_team_edit():
    """ API for editing a team """
    team_id = clean_jsgrid_int(request.form['ID'])
    prjid = None
    prv_id = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    name = request.form['Name']

    return json.dumps(admindb.edit_team_item(myids, name))

@app.route('/data/teams/insert', methods=['POST'])
def admin_team_insert():
    """ API for inserting a team """
    prv_id = None
    team_id = None
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    teamname = request.form['Name']

    return json.dumps(admindb.insert_team_item(myids, teamname))

@app.route('/data/teams/delete', methods=['DELETE'])
def admin_team_delete():
    """ API for deleting a team """
    prv_id = None
    team_id = clean_jsgrid_int(request.form['ID'])
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    teamname = request.form['Name']

    return json.dumps(admindb.delete_team_item(myids, teamname))

@app.route('/data/projects/list', methods=['GET'])
def admin_projects_get():
    """ API for listing/filtering projects """
    prv_id = clean_jsgrid_int(request.args.get('ProviderID'))
    team_id = clean_jsgrid_int(request.args.get('TeamID'))
    bgt_id = None
    prjid = clean_jsgrid_int(request.args.get('ID'))

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    if request.args.get('ExtName') != "":
        name_filter = request.args.get('ExtName')
    else:
        name_filter = None
    if request.args.get('ExtID') != "":
        extid_filter = request.args.get('ExtID')
    else:
        extid_filter = None
    return json.dumps(admindb.get_project_items(myids, name_filter,
                      extid_filter))

@app.route('/data/projects/edit', methods=['POST'])
def admin_project_edit():
    """ API for editing a project """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    bgt_id = None
    prjid = clean_jsgrid_int(request.form['ID'])

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    extname = request.form['ExtName']
    extid = request.form['ExtID']

    return json.dumps(admindb.edit_project_item(myids, extname, extid))

@app.route('/data/projects/insert', methods=['POST'])
def admin_project_insert():
    """ API for inserting a project """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    myextname = request.form['ExtName']
    myextid = request.form['ExtID']

    return json.dumps(admindb.insert_project_item(myids,
                              myextname, myextid))

@app.route('/data/projects/delete', methods=['DELETE'])
def admin_project_delete():
    """ API for deleting a project """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = clean_jsgrid_int(request.form['ID'])
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id)
    myextname = request.form['ExtName']
    myextid = request.form['ExtID']

    return json.dumps(admindb.delete_project_item(myids,
                              myextname, myextid))

def clean_jsgrid_int(my_param):
    """ Handle form parameters caused by js-grid.js """
    if my_param == "0" or my_param == None:
        returnval = None
    else:
        returnval = int(my_param)
    return returnval

