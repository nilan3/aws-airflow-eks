#!/bin/bash

ACCOUNT_ID=""
ENVIRONMENT="dev"
APPLICATION_NAME="airflow"
REGION="eu-west-2"
EC2_KEY_NAME="personal-aws-key"
NODE_IMAGE_ID="ami-097d908f4f4e38dc7"

ACTION=$1

if [[ $ACTION == "setup" ]]
then
	aws cloudformation deploy \
	  --template-file cloudformation/cfn-setup-stack.yml \
	  --stack-name cfn-setup-stack \
	  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
	  --region $REGION \
	  --parameter-overrides Ec2KeyName=${EC2_KEY_NAME} NodeImageId=${NODE_IMAGE_ID} \
	  --no-execute-changeset
elif [[ $ACTION == "deploy" ]]
then
	aws s3 sync cloudformation/templates/ s3://aws-cloudformation-templates-${ENVIRONMENT}-${REGION}/templates/${APPLICATION_NAME}/
	aws cloudformation deploy \
	  --template-file cloudformation/k8s-master-stack.yml \
	  --stack-name $APPLICATION_NAME-k8s-master-stack-$ENVIRONMENT \
	  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
	  --role-arn arn:aws:iam::${ACCOUNT_ID}:role/AWSCloudFormationServiceRole \
	  --region $REGION \
	  --parameter-overrides Ec2KeyName=${EC2_KEY_NAME} NodeImageId=${NODE_IMAGE_ID} \
	  --no-execute-changeset
else
	echo "Invalid argument"
	echo "Usage: cfn-deploy.sh [setup|deploy]"
fi
