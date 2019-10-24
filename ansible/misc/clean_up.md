cd /srv/services/airflow/data/helm-airflow
/usr/local/bin/kubectl apply -f /srv/services/airflow//data/helm-airflow/tiller.yaml
/usr/local/bin/helm init --service-account tiller
/usr/local/bin/helm repo add rancher-latest https://releases.rancher.com/server-charts/latest && /usr/local/bin/helm dep update
/usr/local/bin/kubectl apply -f /srv/services/airflow/conf/airflow-namespace.json
/usr/local/bin/kubectl apply -f /srv/services/airflow/conf/role.yml
/usr/local/bin/kubectl apply -f /srv/services/airflow/conf/manifest.yml -n airflow
/usr/local/bin/kubectl apply -f /srv/services/airflow/conf/nfs-server.yml -n airflow
/usr/local/bin/kubectl apply -f /srv/services/airflow/conf/volumes.yml -n airflow
/usr/local/bin/helm upgrade --force --install airflow /srv/services/airflow/data/helm-airflow/ --namespace airflow --values /srv/services/airflow/conf/dags-volume-readwritemany/values.yaml
/usr/local/bin/kubectl get pods -n airflow
/usr/local/bin/kubectl describe pods -n airflow

/usr/local/bin/kubectl get pods --all-namespaces
/usr/local/bin/kubectl delete ns airflow
helm delete airflow
helm reset --force
/usr/local/bin/kubectl delete -f /srv/services/airflow/conf/role.yml
/usr/local/bin/kubectl delete -f /srv/services/airflow/conf/manifest.yml -n airflow
/usr/local/bin/kubectl delete -f /srv/services/airflow/conf/nfs-server.yml -n airflow
/usr/local/bin/kubectl delete -f /srv/services/airflow/conf/volumes.yml -n airflow


postgres

kubectl exec -ti  -n airflow airflow-postgresql-75bf7d8774-4xwj4 sh
