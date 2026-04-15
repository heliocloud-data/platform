# General config
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

PROJECT_NAME="heliocloud"
ORG_NAME="hsdcloud"
# Backend resource names (S3 bucket names must be globally unique)
BUCKET_NAME="${PROJECT_NAME}-tofu-state-bucket-${ORG_NAME}"
TABLE_NAME="${PROJECT_NAME}-tofu-state-lock-${ORG_NAME}"

# # GitHub OIDC and Role config
# GITHUB_ORG="YourGitHubOrg"
# GITHUB_REPO="YourRepoName"
# ROLE_NAME="GitHubActionsTofuRole"


# 1. Create the bucket
# Note: If you use a region other than us-east-1, the CLI requires a LocationConstraint parameter
if [ "$AWS_REGION" == "us-east-1" ]; then
    aws s3api create-bucket --bucket $BUCKET_NAME --region $AWS_REGION
else
    aws s3api create-bucket --bucket $BUCKET_NAME --region $AWS_REGION --create-bucket-configuration LocationConstraint=$AWS_REGION
fi

# 2. Enable bucket versioning (crucial for state file recovery)
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

# 3. Enable default encryption (AES256)
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

# 4. Block all public access
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"