#!/bin/bash

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
cd /tmp
unzip awscliv2.zip
sudo /tmp/aws/install
rm -rf /tmp/aws/
rm -f /tmp/awscliv2.zip
cd /home/ssm-user

echo "complete -C '/usr/local/bin/aws_completer' aws" >> /home/ssm-user/.bashrc
echo "PATH=$PATH:/usr/local/bin" >> /home/ssm-user/.bashrc
. /home/ssm-user/.bashrc

# Install kubectl.  At the moment, this is a moving target.  We update the URL to point
# to the next stable version of the tool.
#
# See:
#  https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html
sudo curl --location -o /usr/local/bin/kubectl https://s3.us-west-2.amazonaws.com/amazon-eks/1.26.10/2023-11-14/bin/linux/amd64/kubectl
sudo chmod +x /usr/local/bin/kubectl


# Install kustomize.  This is maybe used to patch some 3rd party charts.
#
# See:
#  https://www.tecmint.com/extract-tar-files-to-specific-or-different-directory-in-linux/
#  https://github.com/kubernetes-sigs/kustomize/releases/tag/kustomize%2Fv5.1.1
curl https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.1.1/kustomize_v5.1.1_linux_amd64.tar.gz --silent --location --remote-name
tar zxvf kustomize_v5.1.1_linux_amd64.tar.gz
sudo mv kustomize /usr/local/bin/
rm -rf kustomize_v5.1.1_linux_amd64.tar.gz


# Install eksctl.
#
# See:
#  https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/setting-up-eksctl.html
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 > get_helm.sh
bash get_helm.sh -v v3.9.4
rm -rf get_helm.sh

for command in kubectl jq envsubst aws eksctl helm; do which $command &>/dev/null && echo "OK - $command" || echo "****NOT FOUND IN PATH**** - $command"; done

eksctl completion bash >> /home/ssm-user/.bash_completion
kubectl completion bash >>  /home/ssm-user/.bash_completion

. /etc/profile.d/bash_completion.sh
. /home/ssm-user/.bash_completion