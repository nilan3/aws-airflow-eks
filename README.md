# aws-kubernetes-airflow
Airflow on AWS EKS using Kubernetes executors (deployed with CloudFormation &amp; Ansible)

NOTE:
This is for experimentation purposes only. The configurations are not suitable for production.

Resources extracted and modified from:
- https://github.com/weaveworks/eksctl
- https://amazon-eks.s3-us-west-2.amazonaws.com/cloudformation/2019-09-17/aws-auth-cm.yaml
- https://github.com/apache/airflow/tree/master/scripts/ci/kubernetes

## Usage
Update the variables at the top of `cfn-deploy.sh` script.
Image Id can be obtained from https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html

```
./scripts/cfn-deploy.sh setup
./scripts/cfn-deploy.sh deploy

ansible-playbook -e "ansible_user=ec2-user" -i k8dev setup-site.yml --check --diff
ansible-playbook -e "ansible_user=ec2-user" -i k8dev setup-site.yml --diff
```


## Accessing Airflow Web UI

Run `port-forward` command on bastion ec2 host:

`kubectl port-forward -n airflow service/airflow-web 7000:8080`

SSH tunnel on port 7000 to access the UI from you local environment:

http://127.0.0.1:7000/admin/

You can switch to using loadbalancer by updating airflow service to `type: Loadbalancer` and update security group on eks node group ec2 instances to restrict access as this will be a internet-facing loadbalancer.
