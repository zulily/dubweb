"""
    flask container for all views/html in dubweb
"""
from flask import render_template
from app import app
import app.dubwebdb as dubwebdb
import app.utils as utils

@app.route('/')
@app.route('/index.html')
@app.route('/monthlyprovider.html')
def prov_monthly():
    """  Monthly provider chart and csv """
    return render_template('monthlyprovider.html')

@app.route('/dailyprovider.html')
def prov_daily():
    """  Daily provider chart """
    return render_template('dailyprovider.html')

@app.route('/estimateprovider.html')
def prov_est_monthly():
    """  Monthly provider estimates chart and csv"""
    return render_template('estimateprovider.html')

@app.route('/monthlybudget.html')
def overunder_monthly():
    """  Monthly team budget over/under csv and chart """
    return render_template('monthlybudget.html')

@app.route('/monthlydivision.html')
def div_monthly():
    """  Monthly division chart and csv """
    return render_template('monthlydivision.html')

@app.route('/monthlyteam.html')
def team_monthly():
    """  Monthly team chart and csv """
    return render_template('monthlyteam.html')

@app.route('/dailyteam.html')
def team_daily():
    """  Daily team chart and csv """
    return render_template('dailyteam.html')

@app.route('/estimateteam.html')
def team_est_monthly():
    """  Monthly team estimates chart and csv """
    return render_template('estimateteam.html')

@app.route('/monthlyproject.html')
def project_monthly():
    """  Monthly project chart and csv """
    return render_template('monthlyproject.html')

@app.route('/dailyproject.html')
def project_daily():
    """  Daily project chart """
    return render_template('dailyproject.html')

@app.route('/dailyworkload.html')
def workload_daily():
    """  Daily workload showing google/AWS details per project """
    return render_template('dailyworkload.html')

@app.context_processor
def load_dropdown_lists():
    """  Load the data structures needed for layout.html pages"""
    settings = dict()
    metadata = utils.load_json_definition_file(dubwebdb.SETTINGS_FILE)
    success, db_conn = utils.open_monitoring_db(metadata['dbhost'],
                                                metadata['dbuser'],
                                                metadata['dbpass'],
                                                metadata['db_db'])
    if success:
        providers = dubwebdb.get_providers(provider_id=None,
                                           dub_conn=db_conn)
        settings['providers'] = [item[0] for item in providers.values()]
        settings['prvarray'] = providers
        divisions = dubwebdb.get_divisions(div_ids=None, dub_conn=db_conn)
        settings['divisions'] = [item for item in divisions.values()]
        settings['divhash'] = divisions
        teams = dubwebdb.get_teams(team_ids=None, dub_conn=db_conn)
        settings['teams'] = [item for item in teams.values()]
        settings['teamhash'] = teams
        projects = dubwebdb.get_projects(provider_id=None, team_ids=None,
                                         project_id=None, dub_conn=db_conn)
        settings['projects'] = [item[0] for item in projects.values()]
        settings['prjdict'] = projects
        db_conn.close()

    return dict(settings=settings)
