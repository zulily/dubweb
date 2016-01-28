"""
    flask handler for all capacity API requests for dubweb
"""
from flask import request
from app import app
import app.raxutils as raxutils
import app.capdb as capdb


@app.route('/data/rackspace/host_check')
def cloud_host_check():
    """ API for Rackspace host overload check """
    mydc = request.args.get('dc')
    myvmid = request.args.get('vmid')
    myweight = request.args.get('max_weight')
    return raxutils.check_host_capacity(mydc, myvmid, myweight)

@app.route('/data/rackspace/hostmap')
def cloud_host_map():
    """ API for Rackspace host map chart """
    mydc = request.args.get('dc')
    myacct = request.args.get('acct_id')
    return raxutils.get_vm_hostmap(mydc, myacct)

@app.route('/data/capacity/estimates')
def capacity_estimates():
    """ API for Capacity Estimates chart """
    myids = request.args.get('ids')
    mydate = request.args.get('opt_date')
    mylimits = request.args.get('add_limits')
    return capdb.get_capacity_daily(myids, add_limits=False)

@app.route('/data/capacity/model')
def capacity_model():
    """ API for Capacity Forecast chart """
    myids = request.args.get('ids')
    mydate = request.args.get('opt_date')
    return capdb.get_capacity_model(myids)

@app.route('/data/capacity/actuals')
def capacity_actuals():
    """ API for Capacity Actuals """
    myids = request.args.get('ids')
    mydate = request.args.get('opt_date')
    return capdb.get_monitor_daily(myids, mydate)
