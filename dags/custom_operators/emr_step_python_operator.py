# -*- coding: utf-8 -*-
"""
This is a custom operator class for submitting a python shell job to EMR
"""
import os
import boto3
import time
import logging
from botocore.client import Config
from airflow.operators import BaseOperator
from airflow. utils.decorators import apply_defaults

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()


class EmrClusterException(Exception):
    """
    Exception for unsuccessful step submission to EMR cluster.
    """


class EmrStepPythonOperator(BaseOperator):
    template_fields = ('cluster_name', 'driver_path', 'configuration_path', 'env_variables')
    # ui_color = '#A6E6A6'

    @apply_defaults
    def __init__(self, cluster_name, driver_path, configuration_path,
                 env_variables, *args, **kwargs):
        """
        Operator which takes care of deploying a 'step' onto an existing EMR cluster.
        :param cluster_name: str
        :param driver_path: str - s3 full path for the driver script
        :param configuration_path: str - s3 full path for the job config file
        :param env_variables: dict - environment variable and values
        """
        super(EmrStepPythonOperator, self).__init__(*args, **kwargs)
        self.cluster_name = cluster_name
        self.driver_path = driver_path
        self.configuration_path = configuration_path
        self.env_variables = env_variables

    def check_long_cluster_running(self, emr_connection):
        """
        Method check if long running cluster is active
        Raises Exception if not.
        :param emr_connection: boto3 client
        """
        cluster_list_resp = emr_connection.list_clusters()
        cluster_id = None
        cluster_status = None
        for cluster in cluster_list_resp["Clusters"]:
            if cluster['Name'] == self.cluster_name:
                cluster_id = cluster["Id"]
                cluster_status = cluster["Status"]["State"]
                break
        if not cluster_id:
            raise EmrClusterException("Cluster '{}' does not exist".format(self.cluster_name))
        if cluster_status not in ("RUNNING", "WAITING"):
            raise EmrClusterException("Cluster '{}' is not in RUNNING/WAITING status"
                                      .format(self.cluster_name))
        return cluster_id

    def execute(self, context):
        """
        Method to be run when operator is executed.
        :param context: dict
        """
        config = Config(connect_timeout=5, retries={'max_attempts': 2})
        emr_conn = boto3.client('emr', config=config, region_name='eu-west-1')
        # TODO: Change to using manually specified step name instead of driver filename
        step_action_name = os.path.basename(self.driver_path).replace(".py", "") + "-" + time \
            .strftime("%Y%m%d-%H:%M:%S")
        self.env_variables.update({"STEP_NAME": step_action_name})
        env = " ".join(["{}={}".format(k, self.env_variables[k])
                        for k in self.env_variables])
        sh_script = f"aws s3 cp {self.driver_path} /tmp/ && {env} python3 " \
            f"/tmp/{os.path.basename(self.driver_path)} {self.configuration_path}"
        step_args = ["/bin/sh", "-c", sh_script]
        cluster_id = self.check_long_cluster_running(emr_conn)
        step = {"Name": step_action_name,
                'ActionOnFailure': 'CONTINUE',
                'HadoopJarStep': {
                    'Jar': 's3n://elasticmapreduce/libs/script-runner/script-runner.jar',
                    'Args': step_args}
                }
        action = emr_conn.add_job_flow_steps(JobFlowId=cluster_id, Steps=[step])
        LOGGER.info("Added step: %s", action)
