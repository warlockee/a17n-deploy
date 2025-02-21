helm install airflow apache-airflow/airflow --namespace airflow --values ./custom-values.yaml

# helm upgrade airflow apache-airflow/airflow --namespace airflow --values ./custom-values.yaml

# helm uninstall airflow -n airflow