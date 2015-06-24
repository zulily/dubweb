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
    return dubwebdb.get_data_provider(mytime, myids, True)

@app.route('/data/daily/provider')
def current_chart_provider_daily():
    """ API for daily provider chart """
    mytime = dubwebdb.CTimes("%Y-%m-%d", request.args.get('time_start'),
                    request.args.get('time_end'))
    myids = dubwebdb.Ids(request.args.get('prvid'), request.args.get('teamid'),
                         request.args.get('prjid'))
    return dubwebdb.get_data_provider(mytime, myids, False)

