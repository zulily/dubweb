"""
    flask handler for all admin API/data requests for dubweb
"""
import json
from functools import wraps
from flask import request, Response
from app import app
import app.admindb as admindb
import app.utils as utils

SETTINGS = utils.load_json_definition_file(admindb.SETTINGS_FILE)

# Helpers, which flask requires first
def clean_jsgrid_int(my_param):
    """ Handle form parameters caused by js-grid.js """
    if my_param == "0" or my_param is None:
        returnval = None
    else:
        returnval = int(my_param)
    return returnval

def check_auth(name, pwd):
    """This function is called to check if a username /
    password combination is valid.
    """
    return name == SETTINGS['adm_user'] and pwd == SETTINGS['adm_pass']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(func):
    """ authentication decorator on APIs that Delete/POST admin data """
    @wraps(func)
    def decorated(*args, **kwargs):
        """ checks for basic auth """
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return func(*args, **kwargs)
    return decorated

# Define all admin APIs
@app.route('/data/budgets/list', methods=['GET'])
def admin_budgets_get():
    """ API for listing/filtering budgets """
    prv_id = clean_jsgrid_int(request.args.get('ProviderID'))
    team_id = clean_jsgrid_int(request.args.get('TeamID'))
    bgt_id = clean_jsgrid_int(request.args.get('ID'))
    budget_filter = clean_jsgrid_int(request.args.get('Budget'))
    prjid = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    if request.args.get('Month') != "":
        month_filter = request.args.get('Month')
    else:
        month_filter = None
    return json.dumps(admindb.get_budget_items(myids, month_filter,
                                               budget_filter))

@app.route('/data/budgets/edit', methods=['POST'])
@requires_auth
def admin_budget_edit():
    """ API for editing a budget """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    bgt_id = clean_jsgrid_int(request.form['ID'])
    prjid = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    month = request.form['Month']
    budget = request.form['Budget']
    comment = request.form['Comment']
    response = request.form['Response']

    return json.dumps(admindb.edit_budget_item(myids, month,
                                               budget, comment,
                                               response))

@app.route('/data/budgets/insert', methods=['POST'])
@requires_auth
def admin_budget_insert():
    """ API for inserting a budget """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = None
    bgt_id = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    month = request.form['Month']
    budget = request.form['Budget']
    comment = request.form['Comment']
    response = request.form['Response']

    return json.dumps(admindb.insert_budget_item(myids, month,
                                                 budget, comment,
                                                 response))

@app.route('/data/budgets/delete', methods=['DELETE'])
@requires_auth
def admin_budget_delete():
    """ API for deleting a budget """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    bgt_id = clean_jsgrid_int(request.form['ID'])
    prjid = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    month = request.form['Month']
    budget = request.form['Budget']
    comment = request.form['Comment']

    return json.dumps(admindb.delete_budget_item(myids, month,
                                                 budget, comment))

@app.route('/data/budgets/clone', methods=['POST'])
@requires_auth
def admin_budget_clone():
    """ API for cloning a budget """
    prv_id = None
    team_id = None
    prjid = None
    bgt_id = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    src_month = request.form['source']
    dest_month = request.form['dest']
    if SETTINGS['cloning_ok'] == 1:
        new_bdgts = admindb.clone_budget_month(myids, src_month, dest_month)
        return 'Clone: {0} budgets in {1}.'.format(len(new_bdgts), dest_month)
    else:
        return 'Clone not enabled for this dubweb instance.'

@app.route('/data/providers/list', methods=['GET'])
def admin_providers_get():
    """ API for listing providers """
    prv_id = clean_jsgrid_int(request.args.get('ID'))
    team_id = None
    prjid = None
    bgt_id = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    return json.dumps(admindb.get_providers_admin(myids))

@app.route('/data/teams/list', methods=['GET'])
def admin_teams_get():
    """ API for listing/filtering teams """
    team_id = clean_jsgrid_int(request.args.get('ID'))
    div_id = clean_jsgrid_int(request.args.get('DivisionID'))
    prv_id = None
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    if request.args.get('Name') != "":
        my_name_filter = request.args.get('Name')
    else:
        my_name_filter = None
    return json.dumps(admindb.get_team_items(myids, my_name_filter))

@app.route('/data/teams/edit', methods=['POST'])
@requires_auth
def admin_team_edit():
    """ API for editing a team """
    team_id = clean_jsgrid_int(request.form['ID'])
    div_id = clean_jsgrid_int(request.form['DivisionID'])
    prjid = None
    prv_id = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    name = request.form['Name']

    return json.dumps(admindb.edit_team_item(myids, name))

@app.route('/data/teams/insert', methods=['POST'])
@requires_auth
def admin_team_insert():
    """ API for inserting a team """
    prv_id = None
    team_id = None
    prjid = None
    bgt_id = None

    teamname = request.form['Name']
    div_id = clean_jsgrid_int(request.form['DivisionID'])

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)

    return json.dumps(admindb.insert_team_item(myids, teamname))

@app.route('/data/teams/delete', methods=['DELETE'])
@requires_auth
def admin_team_delete():
    """ API for deleting a team """
    prv_id = None
    team_id = clean_jsgrid_int(request.form['ID'])
    div_id = clean_jsgrid_int(request.form['DivisionID'])
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    teamname = request.form['Name']

    return json.dumps(admindb.delete_team_item(myids, teamname))

@app.route('/data/divisions/list', methods=['GET'])
def admin_divisions_get():
    """ API for listing/filtering divisions """
    div_id = clean_jsgrid_int(request.args.get('ID'))
    team_id = None
    prv_id = None
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    if request.args.get('Name') != "":
        my_name_filter = request.args.get('Name')
    else:
        my_name_filter = None
    return json.dumps(admindb.get_division_items(myids, my_name_filter))

@app.route('/data/divisions/edit', methods=['POST'])
@requires_auth
def admin_division_edit():
    """ API for editing a division """
    div_id = clean_jsgrid_int(request.form['ID'])
    team_id = None
    prjid = None
    prv_id = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    name = request.form['Name']

    return json.dumps(admindb.edit_division_item(myids, name))

@app.route('/data/divisions/insert', methods=['POST'])
@requires_auth
def admin_division_insert():
    """ API for inserting a division """
    prv_id = None
    team_id = None
    prjid = None
    bgt_id = None
    div_id = None

    divname = request.form['Name']

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)

    return json.dumps(admindb.insert_division_item(myids, divname))

@app.route('/data/divisions/delete', methods=['DELETE'])
@requires_auth
def admin_division_delete():
    """ API for deleting a division """
    prv_id = None
    team_id = None
    div_id = clean_jsgrid_int(request.form['ID'])
    prjid = None
    bgt_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    divname = request.form['Name']

    return json.dumps(admindb.delete_division_item(myids, divname))

@app.route('/data/projects/list', methods=['GET'])
def admin_projects_get():
    """ API for listing/filtering projects """
    prv_id = clean_jsgrid_int(request.args.get('ProviderID'))
    team_id = clean_jsgrid_int(request.args.get('TeamID'))
    bgt_id = None
    div_id = None
    prjid = clean_jsgrid_int(request.args.get('ID'))

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
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
@requires_auth
def admin_project_edit():
    """ API for editing a project """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    bgt_id = None
    div_id = None
    prjid = clean_jsgrid_int(request.form['ID'])

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    extname = request.form['ExtName']
    extid = request.form['ExtID']

    return json.dumps(admindb.edit_project_item(myids, extname, extid))

@app.route('/data/projects/insert', methods=['POST'])
@requires_auth
def admin_project_insert():
    """ API for inserting a project """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = None
    bgt_id = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    myextname = request.form['ExtName']
    myextid = request.form['ExtID']

    return json.dumps(admindb.insert_project_item(myids,
                                                  myextname, myextid))

@app.route('/data/projects/delete', methods=['DELETE'])
@requires_auth
def admin_project_delete():
    """ API for deleting a project """
    prv_id = clean_jsgrid_int(request.form['ProviderID'])
    team_id = clean_jsgrid_int(request.form['TeamID'])
    prjid = clean_jsgrid_int(request.form['ID'])
    bgt_id = None
    div_id = None

    myids = admindb.AdmIDs(prv_id, team_id, prjid, bgt_id, div_id)
    myextname = request.form['ExtName']
    myextid = request.form['ExtID']

    return json.dumps(admindb.delete_project_item(myids,
                                                  myextname, myextid))

