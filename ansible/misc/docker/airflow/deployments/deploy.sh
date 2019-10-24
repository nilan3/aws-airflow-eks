#!/usr/bin/env bash

kubectl delete -f deployments/secrets.yml
kubectl delete -f deployments/configmaps.yml
kubectl delete -f deployments/postgres.yml
kubectl delete -f deployments/volumes.yml
kubectl delete -f deployments/airflow.yml

kubectl apply -f deployments/secrets.yml
kubectl apply -f deployments/configmaps.yml
kubectl apply -f deployments/postgres.yml
kubectl apply -f deployments/volumes.yml
kubectl apply -f deployments/airflow.yml
