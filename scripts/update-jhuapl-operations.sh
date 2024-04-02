rm -rf temp

DEST_DIR=jhuapl-operations

export NODE_TLS_REJECT_UNAUTHORIZED=0

export HC_AWS_ACCOUNT=006885615091
export HC_EKS_ROLE_ARN=CT-PowerUser-HelioCloud

export AWS_DEFAULT_REGION=us-east-2
export CI_COMMIT_REF_SLUG=develop
export HC_PORTAL_CERT_ARN="b471d86b-7a52-46cf-a78b-d809f0e313a6"
export CLOUDFORMATION_NAME="stagingdevelopDaskhub400CFEB8"
envsubst < instance/staging.yaml > instance/staging-${CI_COMMIT_REF_SLUG}.yaml
cdk synth staging-${CI_COMMIT_REF_SLUG}/Daskhub -c instance=staging-${CI_COMMIT_REF_SLUG} --require-approval never -v --outputs-file ./cdk-outputs.json --output cdk.synth.out
RET=$?
if [[ $RET != 0 ]]; then
    echo "error: cdk synth failed"
    exit 1
fi

bash scripts/production-to-staging.sh

cp temp/daskhub/deploy/* ${DEST_DIR}/ -R
rm -rf ${DEST_DIR}/heliocloud.code-workspace
rm -rf ${DEST_DIR}/0*sh
rm -rf ${DEST_DIR}/9*sh

# Revert the changes to the Route53 template
cd ${DEST_DIR}
git checkout -- daskhub/route53_record.json.template
cd ..

cd ${DEST_DIR}
echo "bash install-cnf-outputs-to-k8-templates.sh stack-staging.txt staging ${AWS_DEFAULT_REGION} ${CLOUDFORMATION_NAME}"
bash install-cnf-outputs-to-k8-templates.sh stack-staging.txt staging ${AWS_DEFAULT_REGION} ${CLOUDFORMATION_NAME}
cd ..




export AWS_DEFAULT_REGION=us-east-1
export HC_PORTAL_CERT_ARN="fcdaa56d-909d-4edc-8189-95a37d3a2919"
export CLOUDFORMATION_NAME="productionjhuaplDaskhubDB0F7211"
envsubst < instance/production.yaml > instance/production-jhuapl.yaml
cdk synth production-jhuapl/Daskhub -c instance=production-jhuapl --require-approval never -v --outputs-file ./cdk-outputs.json --output cdk.synth.out
RET=$?
if [[ $RET != 0 ]]; then
    echo "error: cdk synth failed"
    exit 1
fi



cp temp/daskhub/deploy/* ${DEST_DIR}/ -R
rm -rf ${DEST_DIR}/heliocloud.code-workspace
rm -rf ${DEST_DIR}/0*sh
rm -rf ${DEST_DIR}/9*sh

cd ${DEST_DIR}
echo "bash install-cnf-outputs-to-k8-templates.sh stack-production.txt production ${AWS_DEFAULT_REGION} ${CLOUDFORMATION_NAME}"
bash install-cnf-outputs-to-k8-templates.sh stack-production.txt production ${AWS_DEFAULT_REGION} ${CLOUDFORMATION_NAME}
cd ..