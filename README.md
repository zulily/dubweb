# DUBWEB - The Datacenter Usage and Billing project
Flask app, db model, and python ETL for tracking/admin/forecasting of datacenter spend. Additional functionality has been added for capacity and datacenter checks.
 
Example datacenter view:
![dubweb datacenter chart](dubweb_monthly_provider.png)


Example admin view:
![dubweb admin grid](dubweb_budget_admin.png)


# Structure

## Root directory
The root directory has the WSGI file. I suggest using nginx, with uwsgi-emperor running flask app as vassals.
 
## /misc directory (Storage)
/misc has the MySQL db model for the dubwebdb.  After creating the database:
1. Populate the providers table, using one row per unique billing provider. 
2. Populate the teams table, using one row per logical team/unit.
3. Populate the projects table, assigning the team and provider to the project.  Note: projects span neither teams nor providers.
4. Populate the budgets table; assign monthly budget for each team's provider.
5. After initial provisioning, you may use the admin pages for modifying teams, projects, and budgets.
6. You may decide to use the matchrules.csv for characterizing workloads

## /etl directory (Collection)
/etl has the python ETL that will pull the data as instructed by the files in the /etl/zu directory. To start collecting data:
Modify `zu_advanced_meta.json` to set DB parameters, metricstypes.
Create a metricstypes file for each separate billing provider:
1. Use the `zu_*_metrics.json` file for the specific type of billing source data given by the billing provider. e.g., Google provides json. 
2. Modify the permetric value, if desired, used in eval for providing:
  - Provider's start time (beginning of day/month metric covers).
  - Provider's project number 
  - Provider's measurement id 
  - Provider's metric measurement (e.g., 24 ) (device/hours)
  - Provider's metric untis (e.g., device/hours)
  - Provider's cost for given product described by metric.
3. Add a "various" list entry for each daily metric that needs all instance metrics for the calculation, but isn't provided by provider  (e.g., Tax):
  - Metric name
  - Provider's start time.
  - Metric id
  - Project id
  - Project name 
  - Metric formula (taxrate is passed into processing function)
  - Team id

### Load the data into DUBWEB once a day by:
1. Copying the provider(s) data file(s) into the zu subdirectory.
2. Loading the data into the DB using:
```
python cub_extract -f zu/zu_advanced_meta.json
```

### If desired, clone the monthly budget to the next month (once a month) by:
1. Ensuring that cloning is enabled in the .admin_settings file.
2. Calling the /misc/clone_month.sh file (after setting your basic auth creds).

## /app directory (web application)
/app has the flask app.  To personalize for your billing needs:
  1. Modify the .*settings files (templates in /misc):
    1. Move the file to a durable location accessible to uwsgi-emperor/nginx
    2. Modify the file to match your DB parameters.
    3. I suggest using different settings files for the different sets of functionality, as the dubwebdb.py functionality only requires SELECT mysql privileges.
  2. Add a new measurement API and chart pair by:
    1. Adding data retrieval function for API to dubwebdb.py.
    2. Add API route to apis.py.
    3. Add template for new measurement/chart in templates, calling new API.
    4. Add chart route to views.py

## /tests directory (unit tests)
/tests has the python unittests: 
  1. Tests for the python modules can be run using nosetests, for example:
```
 nosetests `tests/test_dubwebdb.py`
```

# Dependencies
The project uses the following applications (installed via apt-get, on Ubuntu):
* nginx
* uwsgi_emperor

The project uses the following python packages (installed via pip):
* virtualenv
* Flask
* mysql-python
* python-dateutil
* numpy
* pyfscache
* simplejson
* requests
* functools

