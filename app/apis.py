"""
    flask handler for all customer API requests for dubweb
"""
from app import app
from flask import request
import app.dubwebdb as dubwebdb

# Define all customer APIs
@app.route('/data/monthly/provider')
def current_chart_provider_monthly():
    """ API for monthly provider chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_provider(mytime, myids, add_budget=True)

@app.route('/data/daily/provider')
def current_chart_provider_daily():
    """ API for daily provider chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d",
                             request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_provider(mytime, myids, add_budget=False)

@app.route('/data/monthly/team')
def current_chart_team_monthly():
    """ API for monthly Team chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_team(mytime, myids, add_budget=True)

@app.route('/data/daily/team')
def current_chart_team_daily():
    """ API for daily Team chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_team(mytime, myids, add_budget=False)

@app.route('/data/monthly/project')
def current_chart_project_monthly():
    """ API for monthly Project chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_project(mytime, myids, add_budget=False)

@app.route('/data/daily/project')
def current_chart_project_daily():
    """ API for daily Project chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_project(mytime, myids, add_budget=False)

@app.route('/data/daily/workload')
def current_chart_workload_daily():
    """ API for daily Workload chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_workload(mytime, myids, add_budget=False)

@app.route('/est/monthly/provider')
def future_chart_provider_monthly():
    """ API for estimating monthly provider chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.estimate_data_provider(mytime, myids, add_budget=True)

@app.route('/est/monthly/team')
def future_chart_team_monthly():
    """ API for estimating monthly team chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.estimate_data_team(mytime, myids, add_budget=True)

