# Automate the refresh of your Tableau Dashboards
#### Python automation to bulk refresh tagged Tableau Dashboards via Airflow.
Stop scheduled Extract Refreshes in Tableau and spare your database. This repository contains a set of Tableau api calls in Python with `requests` library to collect all dashboards with a specific tag and bulk refresh them in an Airflow pipeline.

#### Usability
Use the Python Operator to execute the Python callables (tableau.py) in key points of your Airflow data pipeline (dag.py). This way you can ensure that your Tableau dashboards are automatically updated on a regular basis. This is crucial for keeping visualizations current with the latest data.

#### Pre-requisites
* Python 3.7 or above
* Airflow instance
* Generate a Tableau [token](https://help.tableau.com/current/pro/desktop/en-us/useracct.htm#create-a-personal-access-token) and store it as a Variable in Airflow UI

---------------
### For Dashboard Creators (e.g. BI Analysts)
* Simply [tag your dashboard](https://help.tableau.com/current/pro/desktop/en-us/tags.htm#add-tags) with the name of the pipeline (or whatever was agreed with your Data Engineer) where dashboard should be triggered. 
* A dashboard can be refreshed in several Airflow pipelines, thus multiple tags can be assigned.

### For Data Engineers
* A Tableau token should be created per pipeline to avoid [concurrent connections](https://github.com/tableau/server-client-python/issues/717).
