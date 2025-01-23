# helm install airflow apache-airflow/airflow --namespace airflow --values ./custom-values.yaml

helm upgrade airflow apache-airflow/airflow --namespace airflow --values ./custom-values.yaml

# helm uninstall airflow -n airflow

# kubectl get pods -n airflow \
#   | grep Terminating \
#   | awk '{print $1}' \
#   | xargs kubectl delete pod -n airflow --grace-period=0 --force