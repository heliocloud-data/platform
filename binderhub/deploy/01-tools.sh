#!/bin/bash

sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
sudo yum -y install jq gettext bash-completion moreutils docker unzip nano git


curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
cd /tmp
unzip awscliv2.zip
sudo /tmp/aws/install
rm -rf /tmp/aws/
rm -f /tmp/awscliv2.zip
cd ~

sudo curl --location -o /usr/local/bin/kubectl https://s3.us-west-2.amazonaws.com/amazon-eks/1.22.6/2022-03-09/bin/linux/amd64/kubectl
sudo chmod +x /usr/local/bin/kubectl

#curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
curl --silent --location "https://github.com/weaveworks/eksctl/releases/download/v0.111.0/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# this installs the current default.
# curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
# you may want to do this instead:
#
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 > get_helm.sh
bash get_helm.sh -v v3.9.4

for command in kubectl jq envsubst aws eksctl helm; do which $command &>/dev/null && echo "OK - $command" || echo "****NOT FOUND IN PATH**** - $command"; done


echo "complete -C '/usr/local/bin/aws_completer' aws" >> ~/.bashrc
. ~/.bashrc

eksctl completion bash >> ~/.bash_completion
kubectl completion bash >>  ~/.bash_completion

. /etc/profile.d/bash_completion.sh
. ~/.bash_completion

AWS_REGION=$(curl -s curl http://169.254.169.254/latest/meta-data/placement/region)

aws configure set output json
aws configure set region $AWS_REGION
