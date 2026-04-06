
BUCKET_NAME=$0
OUTPUT_LIST=$1

# 1. get a list of all current object on bucket
# # you can use an output of the s3_comparison find_missing_files_in_dest.sh script

# 2. Create a list of shell commands to execute
cmds=`python make_delete_script.py -b $BUCKET_NAME -o $OUTPUT_LIST`
echo $cmds

# 3. Execute commands to delete data
$cmds

echo "Finished"
