# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
FROM python:3.6-slim

# install deps
RUN apt-get update -y && apt-get install -y \
        wget \
        libczmq-dev \
        curl \
        libssl-dev \
        git \
        libpq-dev \
        inetutils-telnet \
        bind9utils \
        zip \
        unzip \
        gcc \
    && apt-get clean

RUN pip install --upgrade pip

# Since we install vanilla Airflow, we also want to have support for Postgres and Kubernetes
RUN pip install -U setuptools && \
    pip install kubernetes && \
    pip install cryptography && \
    pip install psycopg2-binary==2.7.4 && \
    pip install boto3 && \
    pip install awscli

# install airflow
RUN pip install apache-airflow[crypto,postgres,jdbc,ssh,kubernetes]==1.10.5

COPY airflow-test-env-init.sh /tmp/airflow-test-env-init.sh
RUN chmod +x /tmp/airflow-test-env-init.sh

COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /bootstrap.sh

ENTRYPOINT ["/bootstrap.sh"]
