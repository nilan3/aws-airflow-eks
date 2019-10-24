# -*- coding: utf-8 -*-
"""
DAG to execute E2E Pipeline for GuildWire PolicyCenter data.
"""

__version_info__ = (2019, 10, 23)
__version__ = '{0}.{1}.{2}'.format(*__version_info__)

from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
import sys
import datetime
import logging

try:
    from airflow.dags.custom_operators.emr_step_operator import EmrClusterException, EmrStepOperator
    from airflow.dags.custom_operators.dynamo_sensor_operator import DynamoSensorOperator
except ModuleNotFoundError:
    custom_operators_path = "/root/airflow/dags/repo/dags"
    if custom_operators_path not in sys.path:
        sys.path.append(custom_operators_path)
    from custom_operators.emr_step_operator import EmrClusterException, EmrStepOperator
    from custom_operators.dynamo_sensor_operator import DynamoSensorOperator

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()

dag = DAG(
    dag_id='Guildwire_PolicyCenter_E2E_Pipeline',
    default_args={
        'owner': 'Airflow',
        'start_date': datetime.datetime(2019, 9, 8)
    },
    schedule_interval=None,
    start_date=datetime.datetime(2019, 9, 8))


def initiate_csv_to_parquet():
    print("CSV to Parquet Jobs!")


def initiate_spark():
    print("Spark Job!")


def dynamodb_sensor_processor(items, boto3_client):
    """
    Processor for applying conditions on items return from Dynomodb Query.
    :param items: list of table items
    :param boto3_client: boto3
    :return: Boolean
    """
    time_threshold_min = 5
    if not items:
        return False
    item = items[0]
    if item["status"]["S"] in ["failed", "done"]:
        ts = datetime.datetime.strptime("-".join(item["job_name"]["S"].split("-")[-2:]), "%Y%m%d-%H:%M:%S")
        ts_threshold = datetime.datetime.now() - datetime.timedelta(minutes=time_threshold_min)
        if ts <= ts_threshold:
            return False
    ddb_conn = boto3_client.client('dynamodb', region_name='eu-west-1')
    if item["status"]["S"] == "processed":
        item.update({"status": {'S': 'done'}})
        ddb_conn.put_item(
            TableName="policycentre_pipeline_control",
            Item=item)
        return True
    emr_conn = boto3_client.client('emr', region_name='eu-west-1')
    emr_clusters = emr_conn.list_clusters()
    emr_cluster_name = "DataPipeline-EMR-sandbox"
    cluster_id = None
    for cluster in emr_clusters["Clusters"]:
        if cluster['Name'] == emr_cluster_name:
            cluster_id = cluster["Id"]
            break
    if not cluster_id:
        raise Exception("Cluster '{}' does not exist".format(emr_cluster_name))
    # TODO: improve method to use pagination token
    steps = emr_conn.list_steps(ClusterId=cluster_id)["Steps"]
    for step in steps:
        if step["Name"] == item["job_name"]["S"]:
            if step["Status"]["State"] in ['CANCELLED', 'FAILED', 'INTERRUPTED']:
                # TODO: Fetch Error
                item.update({"status": {'S': 'failed'}})
                ddb_conn.put_item(
                    TableName="policycentre_pipeline_control",
                    Item=item)
                raise Exception("EMR Step {} has failed".format(item["job_name"]["S"]))
            else:
                return True
    return False


initiate_csv_to_parquet_jobs = PythonOperator(
    task_id="initiate_csv_to_parquet_jobs", python_callable=initiate_csv_to_parquet, dag=dag,
    executor_config={"KubernetesExecutor": {"image": "nilan3/airflow-k8s:test-local-3"}}
)

pc_etlclausepattern_task = EmrStepOperator(
    task_id="pc_etlclausepattern_task",
    executor_config={"KubernetesExecutor": {
        "image": "nilan3/airflow-k8s:test-local-3"
    }},
    cluster_name="DataPipeline-EMR-sandbox",
    driver_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/drivers/csv_to_parquet.py",
    step_name="csv2parquet_pc_etlclausepattern",
    configuration_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/configurations/emr-csv-to-parquet.yml",
    env_variables={
        "PY_FILES": "s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/py-files/dlg-etl-quotes.zip",
        "SRC_S3_PREFIX": "PCUSER/PC_ETLCLAUSEPATTERN"
    },
    mode="python"
)

pcx_mottransaction_task = EmrStepOperator(
    task_id="pc_account_task",
    executor_config={"KubernetesExecutor": {
        "image": "nilan3/airflow-k8s:test-local-3"
    }},
    cluster_name="DataPipeline-EMR-sandbox",
    driver_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/drivers/csv_to_parquet.py",
    step_name="csv2parquet_pc_account",
    configuration_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/configurations/emr-csv-to-parquet.yml",
    env_variables={
        "PY_FILES": "s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/py-files/dlg-etl-quotes.zip",
        "SRC_S3_PREFIX": "PCUSER/PCX_MOTTRANSACTION_DLG"
    },
    mode="python"
)

pcx_motcost_task = EmrStepOperator(
    task_id="pc_account_task",
    executor_config={"KubernetesExecutor": {
        "image": "nilan3/airflow-k8s:test-local-3"
    }},
    cluster_name="DataPipeline-EMR-sandbox",
    driver_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/drivers/csv_to_parquet.py",
    step_name="csv2parquet_pc_account",
    configuration_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/configurations/emr-csv-to-parquet.yml",
    env_variables={
        "PY_FILES": "s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/py-files/dlg-etl-quotes.zip",
        "SRC_S3_PREFIX": "PCUSER/PCX_MOTCOST_DLG"
    },
    mode="python"
)

pc_etlclausepattern_sensor_task = DynamoSensorOperator(
    task_id="pc_etlclausepattern_sensor_task",
    executor_config={"KubernetesExecutor": {
        "image": "nilan3/airflow-k8s:test-local-3"
    }},
    table_name="policycentre_pipeline_control",
    key_condition_expr="#S = :schema_table_name AND #T > :time_stamp",
    expr_attr_names={"#S": "schema_table", "#T": "ts"},
    expr_attr_values={":schema_table_name": {"S": "PCUSER_PC_ETLCLAUSEPATTERN"},
                      ":time_stamp": {"N": str(int(datetime.datetime.now().timestamp()) - (24*60*60))}},
    limit=1,
    processor=dynamodb_sensor_processor
)

pcx_mottransaction_sensor_task = DynamoSensorOperator(
    task_id="pc_account_sensor_task",
    executor_config={"KubernetesExecutor": {
        "image": "nilan3/airflow-k8s:test-local-3"
    }},
    table_name="policycentre_pipeline_control",
    key_condition_expr="#S = :schema_table_name AND #T > :time_stamp",
    expr_attr_names={"#S": "schema_table", "#T": "ts"},
    expr_attr_values={":schema_table_name": {"S": "PCUSER_PCX_MOTTRANSACTION_DLG"},
                      ":time_stamp": {"N": str(int(datetime.datetime.now().timestamp()) - (24*60*60))}},
    limit=1,
    processor=dynamodb_sensor_processor
)

pcx_motcost_sensor_task = DynamoSensorOperator(
    task_id="pc_account_sensor_task",
    executor_config={"KubernetesExecutor": {
        "image": "nilan3/airflow-k8s:test-local-3"
    }},
    table_name="policycentre_pipeline_control",
    key_condition_expr="#S = :schema_table_name AND #T > :time_stamp",
    expr_attr_names={"#S": "schema_table", "#T": "ts"},
    expr_attr_values={":schema_table_name": {"S": "PCUSER_PCX_MOTCOST_DLG"},
                      ":time_stamp": {"N": str(int(datetime.datetime.now().timestamp()) - (24*60*60))}},
    limit=1,
    processor=dynamodb_sensor_processor
)

initiate_spark_job = PythonOperator(
    task_id="initiate_spark_job", python_callable=initiate_spark, dag=dag,
    executor_config={"KubernetesExecutor": {"image": "nilan3/airflow-k8s:test-local-3"}}
)

# curation_spark_job = EmrStepOperator(
#     task_id="join_curate_task", dag=dag,
#     executor_config={"KubernetesExecutor": {
#         "image": "nilan3/airflow-k8s:test-local-3"
#     }},
#     cluster_name="DataPipeline-EMR-sandbox",
#     driver_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/drivers/csv_to_parquet.py",
#     step_name="pc_policy_transaction",
#     configuration_path="s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/configurations/emr-csv-to-parquet.yml",
#     env_variables={
#         "PY_FILES": "s3://dlg-artefacts-bucket-sandbox-eu-west-1/emr/py-files/dlg-etl-quotes.zip",
#         "SRC_S3_PREFIX": "PCUSER/PC_ACCOUNT"
#     },
#     mode="python"
#
# )

initiate_csv_to_parquet_jobs >> [pc_etlclausepattern_task, pcx_mottransaction_task, pcx_motcost_task]
pc_etlclausepattern_task >> pc_etlclausepattern_sensor_task
pcx_mottransaction_task >> pcx_mottransaction_sensor_task
pcx_motcost_task >> pcx_motcost_sensor_task
[pc_etlclausepattern_sensor_task, pcx_mottransaction_sensor_task, pcx_motcost_sensor_task] >> initiate_spark_job
