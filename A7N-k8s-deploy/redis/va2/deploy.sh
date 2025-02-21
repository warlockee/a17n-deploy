helm install redis-cluster bitnami/redis-cluster -n redis \
  -f custom-values.yaml

# helm delete redis-cluster --namespace redis

#  kubectl delete pvc -l app.kubernetes.io/instance=redis-cluster