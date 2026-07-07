#/bin/bash

EKS_CLUSTER_NAME=$1

if [[ "${EKS_CLUSTER_NAME}" == "" ]]; then
    echo "error: missing eks-cluster-name"
    echo "usage: ${0} <eks-cluster-name>"
    echo ""
    exit 1
fi

NODEGROUP_LIST_FILE=.cluster.${EKS_CLUSTER_NAME}.nodegroups.txt
rm -rf $NODEGROUP_LIST_FILE

eksctl get nodegroups --cluster=$EKS_CLUSTER_NAME -o json | jq '.[].Name' | sed 's#"##g' > $NODEGROUP_LIST_FILE

for NODEGROUP_NAME in $(cat $NODEGROUP_LIST_FILE); do
    echo "Updating nodegroup: $NODEGROUP_NAME"
    aws eks update-nodegroup-version --cluster-name $EKS_CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME
done
