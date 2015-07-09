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

@app.route('/monthlyteam.html')
def team_monthly():
    """  Monthly team web page, which uses jquery to load
         monthly team API """
    return render_template('monthlyteam.html')

@app.route('/dailyteam.html')
def team_daily():
    """  Daily team web page, which uses jquery to load
         daily team API """
    return render_template('dailyteam.html')

@app.route('/monthlyproject.html')
def project_monthly():
    """  Monthly project web page, which uses jquery to load
         monthly project API """
    return render_template('monthlyproject.html')

@app.route('/dailyproject.html')
def project_daily():
    """  Daily project web page, which uses jquery to load
         daily project API """
    return render_template('dailyproject.html')

@app.route('/dailyworkload.html')
def workload_daily():
    """  Daily workload web page, which uses jquery to load
         daily workload API """
    return render_template('dailyworkload.html')

@app.route('/budgets.html')
def admin_budgets():
    """  Budgets web page with data grid
         """
    return render_template('budgets.html')

@app.route('/providers.html')
def admin_providers():
    """  Providers web page with data grid
         """
    return render_template('providers.html')

@app.route('/teams.html')
def admin_teams():
    """  Teams web page with data grid
         """
    return render_template('teams.html')

@app.route('/projects.html')
def admin_projects():
    """  Projects web page with data grid
         """
    return render_template('projects.html')

@app.context_processor
def load_dropdown_lists():
    """  Load the data structures needed for layout.html,
         used as top navigation in all pages """
    settings = dict()
    metadata = utils.load_json_definition_file("/var/dubweb/.settings")
    success, db_conn = utils.open_monitoring_db(
                            metadata['dbhost'], metadata['dbuser'],
                            metadata['dbpass'], metadata['db_db'])
    if success:
        providers = dubwebdb.get_providers(provider_id=None,
                                           dub_conn=db_conn)
        settings['providers'] = [item[0] for item in providers.values()]
        settings['prvarray'] = providers
        teams = dubwebdb.get_teams(team_id=None, dub_conn=db_conn)
        settings['teams'] = [item for item in teams.values()]
        settings['teamhash'] = teams
        projects = dubwebdb.get_projects(provider_id=None, team_id=None,
                                         project_id=None, dub_conn=db_conn)
        settings['projects'] = [item[0] for item in projects.values()]
        settings['prjdict'] = projects

    return dict(settings=settings)

