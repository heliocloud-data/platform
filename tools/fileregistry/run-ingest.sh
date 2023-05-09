date
echo "Running Ingester Lambda"
aws lambda invoke \
    --cli-binary-format raw-in-base64-out \
    --invocation-type Event \
    --function-name Ingester \
    --payload '{ "upload_path" : "s3://cjeschke-dev-uploads/mms_201509_upload/", "manifest" : "manifest.csv", "entry" : "entry.json" }' \
    results.json
date
