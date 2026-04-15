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

# Create dynamodb table to store state lock files
aws dynamodb create-table \
  --table-name $TABLE_NAME \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION