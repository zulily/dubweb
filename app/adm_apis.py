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
    """  Handle jsGrid default of "0"  """
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
    """  Handle jsGrid default of "0"  """
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
    """  Handle jsGrid default of "0"  """
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
    """ API for editing a budget """
    """  Handle jsGrid default of "0"  """
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

def clean_jsgrid_int(x):
    if x == "0" or x == None:
        rv = None
    else:
        rv = int(x)
    return rv

