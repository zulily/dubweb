"""
    flask container for capacity views/html in dubweb
"""
from flask import render_template
from app import app
import app.utils as utils
import app.capdb as capdb


@app.route('/hostmap.html')
def datacenter_hostmap():
    """  Hostmap web page, which uses jquery to load
         datacenter hostmap API """
    return render_template('hostmap.html')

@app.route('/capacity.html')
def capacity_reports():
    """  Capacity chart web page, which uses jquery to load
         capacity estimates API """
    return render_template('capacity.html')

@app.context_processor
def load_cap_dropdowns():
    """  Load the data structures needed for layout_cap.html capacity pages"""
    settings = dict()
    metadata = utils.load_json_definition_file(capdb.SETTINGS_FILE)
    success, cdb_conn = utils.open_monitoring_db(metadata['cdbhost'],
                                                 metadata['cdbuser'],
                                                 metadata['cdbpass'],
                                                 metadata['cdb_db'])
    if success:
        capmetrics = capdb.get_cap_ids(cap_ids=None, cap_conn=cdb_conn)
        settings['caparray'] = capmetrics
        cdb_conn.close()

    return dict(csettings=settings)
