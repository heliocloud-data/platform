
INPUT=$1
BUCKET='helio-data-staging'
OUTPUT_LIST='s3_delete_obs.csv'

# 0. copy input list 
echo "cp $1 s3_delete_obs.csv"
cp $1 s3_delete_obs.csv

# 1. trim off trailing
echo "sed 's/,.*//' -i s3_delete_obs.csv" 
sed 's/,.*//' -i s3_delete_obs.csv

# 1. get a list of all current object on bucket
#echo "python make_objlist.py -b $BUCKET -a -o $OUTPUT_LIST"
#python make_objlist.py -b $BUCKET -a -o $OUTPUT_LIST

# 2. Create a list of shell commands to execute
cmds=`python make_delete_script.py -b helio-data-staging -o $OUTPUT_LIST > delete.sh`
echo $cmds
$cmds

# 3. Execute command to run the delete script 
echo "Finished - Now run the command 'sh delete.sh'" 
# sh delete.sh

