# Initial Setup

Ensure you have the necessary access delegated to your user/role prior to setup and export your aws credentials.

Prior to running any tofu commands, you will need to run the scripts "create_backend_state_s3.sh" and "create_dynamodb.sh"
to setup your backend configurations. Replace the values within the top block prior to running the bash commands - this makes sure to
create the backend storage in you specific AWS account.

example top block:

    AWS_REGION="us-east-2"
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

    PROJECT_NAME="heliocloud"
    ORG_NAME="hsdcloud"
    # Backend resource names (S3 bucket names must be globally unique)
    BUCKET_NAME="${PROJECT_NAME}-tofu-state-bucket-${ORG_NAME}"
    TABLE_NAME="${PROJECT_NAME}-tofu-state-lock-${ORG_NAME}"

