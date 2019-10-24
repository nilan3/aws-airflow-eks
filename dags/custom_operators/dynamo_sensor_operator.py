# -*- coding: utf-8 -*-
"""
This is a custom sensor operator class for querying dynamodb and applying a check function on resulting item(s)
"""
import boto3
import time
from botocore.client import Config
from airflow.sensors.base_sensor_operator import BaseSensorOperator
from airflow.utils.decorators import apply_defaults


class DynamoSensorOperator(BaseSensorOperator):
    template_fields = ('table_name', 'key_condition_expr', 'expr_attr_names',
                       'expr_attr_values', 'limit', 'processor')
    # ui_color = '#A6E6A6'

    @apply_defaults
    def __init__(self, table_name, key_condition_expr, expr_attr_names, expr_attr_values,
                 limit, processor, *args, **kwargs):
        """
        Sensor Operator to query Dynamodb Table and apply a check on the returned items
        :param table_name:
        :param key_condition_expr:
        :param expr_attr_names:
        :param expr_attr_values:
        :param limit:
        :param processor:
        :param args:
        :param kwargs:
        """
        super(DynamoSensorOperator, self).__init__(*args, **kwargs)
        self.table_name = table_name
        self.key_condition_expr = key_condition_expr
        self.expr_attr_names = expr_attr_names
        self.expr_attr_values = expr_attr_values
        self.limit = limit
        self.processor = processor

    def poke(self, context):
        # time.sleep(10)
        config = Config(connect_timeout=5, retries={'max_attempts': 2})
        ddb_conn = boto3.client('dynamodb', config=config, region_name="eu-west-1")
        items = ddb_conn.query(
            Limit=self.limit,
            ScanIndexForward=False,
            TableName=self.table_name,
            KeyConditionExpression=self.key_condition_expr,
            ExpressionAttributeNames=self.expr_attr_names,
            ExpressionAttributeValues=self.expr_attr_values
        )["Items"]
        return self.processor(items, boto3)
