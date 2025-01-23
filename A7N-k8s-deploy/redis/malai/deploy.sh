# helm install redis-cluster bitnami/redis-cluster -n redis \
#   --set cluster.nodes=40 \
#   --set cluster.replicas=2 \
#   --set persistence.storageClass="ddnfs01" \
#   --set persistence.size="10Gi" \
#   --set resources.requests.cpu="2" \
#   --set resources.requests.memory="16Gi" \
#   --set resources.limits.cpu="4" \
#   --set resources.limits.memory="32Gi" \
#   --set auth.enabled=true \
#   --set auth.password="admin"

# helm delete redis-cluster --namespace redis

#  kubectl delete pvc -l app.kubernetes.io/instance=redis-cluster

helm install redis-cluster bitnami/redis-cluster -n redis -f custom-values.yaml
