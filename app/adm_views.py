"""
    flask container for admin views/html in dubweb
"""
from flask import render_template
from app import app
import app.dubwebdb as dubwebdb
import app.admindb as admindb
import app.utils as utils

ADM_SETTINGS = utils.load_json_definition_file(admindb.SETTINGS_FILE)

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
def load_adm_dropdowns():
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
        teams = dubwebdb.get_teams(team_id=None, dub_conn=db_conn)
        settings['teams'] = [item for item in teams.values()]
        settings['teamhash'] = teams
        projects = dubwebdb.get_projects(provider_id=None, team_id=None,
                                         project_id=None, dub_conn=db_conn)
        settings['projects'] = [item[0] for item in projects.values()]
        settings['prjdict'] = projects
        settings['enable_cloning'] = ADM_SETTINGS['cloning_ok']
        db_conn.close()

    return dict(asettings=settings)
