from airflow.models import Variable

# Airflow Variable containing all Tableau tokens
TABLEAU_TOKENS = Variable.get("tableau_tokens", deserialize_json=True)
MY_PIPELINE = "my_pipeline"