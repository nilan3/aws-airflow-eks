#!/usr/bin/env bash

IMAGE=nilan3/airflow-k8s
TAG=test-local-2

set -e

docker build --pull "." --tag="${IMAGE}:${TAG}"
