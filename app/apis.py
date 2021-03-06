"""
    flask handler for all usage API requests for dubweb
"""
import time
import csv
import StringIO
from flask import request, make_response
from app import app
import app.dubwebdb as dubwebdb

# Define all customer APIs
@app.route('/data/monthly/provider')
def current_chart_provider_monthly():
    """ API for monthly provider chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    csv_only = request.args.get('dl_csv')
    if csv_only:
        myrows = dubwebdb.get_data_budget_provider(mytime, myids)
        return convert_to_download_csv(myrows)
    else:
        return dubwebdb.get_data_provider(mytime, myids, add_budget=True)

@app.route('/data/monthly/overunder')
def current_chart_overunder_monthly():
    """ API for monthly provider chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    csv_only = request.args.get('dl_csv')
    if csv_only:
        myrows = dubwebdb.get_budget_over_under(mytime, myids)
        return convert_to_download_csv(myrows)
    else:
        return dubwebdb.get_data_provider(mytime, myids, add_budget=True)


@app.route('/data/daily/provider')
def current_chart_provider_daily():
    """ API for daily provider chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d",
                             request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    return dubwebdb.get_data_provider(mytime, myids, add_budget=False)

@app.route('/data/monthly/team')
def current_chart_team_monthly():
    """ API for monthly Team chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    csv_only = request.args.get('dl_csv')
    if csv_only:
        myrows = dubwebdb.get_data_budget_team(mytime, myids)
        return convert_to_download_csv(myrows)
    else:
        return dubwebdb.get_data_team(mytime, myids, add_budget=True)

@app.route('/data/monthly/division')
def current_chart_division_monthly():
    """ API for monthly Division chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=None,
                         project_id=request.args.get('prjid'),
                         div_id=sanitize_list(request.args.get('divid')))
    csv_only = request.args.get('dl_csv')
    if csv_only:
        myrows = dubwebdb.get_data_budget_div(mytime, myids)
        return convert_to_download_csv(myrows)
    else:
        return dubwebdb.get_data_div(mytime, myids, add_budget=True)

@app.route('/data/daily/team')
def current_chart_team_daily():
    """ API for daily Team chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    return dubwebdb.get_data_team(mytime, myids, add_budget=False)

@app.route('/data/monthly/project')
def current_chart_project_monthly():
    """ API for monthly Project chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    csv_only = request.args.get('dl_csv')
    if csv_only:
        myrows = dubwebdb.get_data_item_cost(mytime, myids)
        return convert_to_download_csv(myrows)
    else:
        return dubwebdb.get_data_project(mytime, myids, add_budget=False)

@app.route('/data/daily/project')
def current_chart_project_daily():
    """ API for daily Project chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    return dubwebdb.get_data_project(mytime, myids, add_budget=False)

@app.route('/data/daily/workload')
def current_chart_workload_daily():
    """ API for daily Workload chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=request.args.get('prvid'),
                         team_id=request.args.get('teamid'),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    return dubwebdb.get_data_workload(mytime, myids, add_budget=False)

@app.route('/est/monthly/provider')
def future_chart_provider_monthly():
    """ API for estimating monthly provider chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    return dubwebdb.estimate_data_provider(mytime, myids, add_budget=True)

@app.route('/est/monthly/team')
def future_chart_team_monthly():
    """ API for estimating monthly team chart """
    mytime = dubwebdb.CTimes("%Y-%m", request.args.get('time_start'),
                             request.args.get('time_end'))
    myids = dubwebdb.Ids(prv_id=sanitize_list(request.args.get('prvid')),
                         team_id=sanitize_list(request.args.get('teamid')),
                         project_id=request.args.get('prjid'),
                         div_id=None)
    return dubwebdb.estimate_data_team(mytime, myids, add_budget=True)

def convert_to_download_csv(rows):
    """
    Given a list with header and body rows,
    Return an http response that will be downloaded as csv
    """
    timestr = time.strftime("%Y%m%d_%H%M%S")
    content_disp = "attachment; filename=export_" + timestr + ".csv"
    sio = StringIO.StringIO()
    cwrtr = csv.writer(sio)
    cwrtr.writerows(rows)
    output = make_response(sio.getvalue())
    output.headers["Content-Disposition"] = content_disp
    output.headers["Content-type"] = "text/csv"
    return output

def sanitize_list(mylist):
    """ Helper function to objectify items """
    if mylist is not None:
        return mylist.split(',')
    else:
        return None

