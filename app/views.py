"""
    flask container for all views/html in dubweb
"""
from app import app
from flask import render_template
import app.dubwebdb as dubwebdb
import app.utils as utils

@app.route('/')
@app.route('/index.html')
@app.route('/monthlyprovider.html')
def prov_monthly():
    """  Monthly provider web page, which uses jquery to load
         monthly provider API """
    return render_template('monthlyprovider.html')

@app.route('/dailyprovider.html')
def prov_daily():
    """  Daily provider web page, which uses jquery to load
         daily provider API """
    return render_template('dailyprovider.html')

@app.route('/budgets.html')
def admin_budgets():
    """  Budgets web page with data grid
         """
    return render_template('budgets.html')

@app.context_processor
def load_dropdown_lists():
    """  Load the data structures needed for layout.html,
         used as top navigation in all pages """
    settings = dict()
    metadata = utils.load_json_definition_file("/var/dubweb/.settings")
    success, db_conn = utils.open_monitoring_db(
                            metadata['dbhost'], metadata['dbuser'],
                            metadata['dbpass'], metadata['db_db'])
    providers = dubwebdb.get_providers(provider_id=None,
                                       dub_conn=db_conn)
    settings['providers'] = [item[0] for item in providers.values()]
    settings['prvarray'] = providers
    teams = dubwebdb.get_teams(team_id=None, dub_conn=db_conn)
    settings['teamhash'] = teams
    projects = dubwebdb.get_projects(provider_id=None, team_id=None,
                                     project_id=None, dub_conn=db_conn)
    settings['prjdict'] = projects

    return dict(settings=settings)

