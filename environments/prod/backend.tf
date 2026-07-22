terraform {
  backend "s3" {
    # We will pass bucket, key, region, and dynamodb_table at init time
    encrypt = true
  }
}