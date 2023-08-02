import cdflib
import boto3
from datetime import datetime as dt
import glob
import os
import decimal

dynamodb = boto3.resource("dynamodb")


def retrieve_object(meta_data):
    """
    Loads the CDF file using S3-aware cdflib, pulls out the relevant information,
    Dumps to dynamoDB for registry
    :param s3_bucket:
    :param s3_filename:
    :return:
    """
    # determine if the tmp directory is already full and if so delete anything in it
    if glob.glob("/tmp/*"):
        for i in glob.glob("/tmp/*"):
            os.remove(i)

    # make a session for the bucket
    s3 = boto3.client("s3")

    s3_bucket = meta_data["s3_bucket"]
    s3_filename = meta_data["s3_filename"]
    s3.download_file(s3_bucket, s3_filename, "/tmp/fileobj.cdf")

    # try:
    # will raise an error if the validation fails - other errors could also happen
    cdfobj = cdflib.CDF("/tmp/fileobj.cdf", validate=True)
    cdf_item, cdf_vars = get_cdf_attributes(cdfobj, meta_data)

    return cdf_item, cdf_vars


def get_cdf_attributes(cdf_file, meta_data):
    """
    Pulls out the CDF attributes for storage in the dynamoDB
    :param cdf_file:
    :return:
    """
    cdf_info = cdf_file.cdf_info()

    # grab the version number if present
    try:
        version = cdf_info["Version"]
    except:
        version = ""

    # grab all of the variables
    zvars = cdf_info["zVariables"]

    # grab the start and stop time of the file
    # this will spit out a time string which divees down into microseconds
    epoch_time = cdf_file.varget("Epoch")
    start_time = cdflib.cdfepoch.encode(epoch_time[0])
    end_time = cdflib.cdfepoch.encode(epoch_time[-1])
    start_time_epoch = cdflib.cdfepoch.unixtime(epoch_time[0])[0]
    end_time_epoch = cdflib.cdfepoch.unixtime(epoch_time[-1])[0]

    # get the current date
    upload_date = dt.now().isoformat()

    print("Start time = {}".format(start_time))
    print("End time = {}".format(end_time))

    # edit the mission to be a concatenation of mission and spacecraft if a spacecraft field is present
    if meta_data["sc"]:
        mission = "_".join([meta_data["mission"], meta_data["sc"]])
    else:
        mission = meta_data["mission"]

    # create a dictionary of all the relevant attributes to be used for upload
    item_dict = {
        "s3_filekey": meta_data["s3_filename"],
        "dataset": meta_data["dataset"],
        "start_date": start_time,
        "end_date": end_time,
        "mission": mission,
        "instrument": meta_data["instr"],
        "level_processing": meta_data["level_proc"],
        "dataset_update": upload_date,
        "source_update": meta_data["source_update"],
        "version": version,
    }

    vars = set(zvars)
    return item_dict, vars


def register_item(db_item):
    """
    Establish a connection with the DynamoDB Table and register the object
    :param db_item:
    :return:
    """
    filereg_table = dynamodb.Table("fileRegister")
    filereg_table.put_item(Item=db_item)


def update_summary_table(db_item, in_newitem_vars):
    """
    Update the summary table to account for the new object being registered
    """
    summary_table = dynamodb.Table("dataSummary")
    # query table for this data product
    response = summary_table.get_item(
        Key={"mission": db_item["mission"], "dataset": db_item["dataset"]}
    )
    if "Item" in response:
        item = response["Item"]
        # determine if any relevant parameters have been changed in the file
        date_range_change = False
        variable_change = False

        # first compare the date range
        if (item["dataset_start"] > db_item["start_date"]) | (
            item["dataset_end"] < db_item["end_date"]
        ):
            date_range_change = True

        # second compare the variables
        in_table_vars = set(item["variables"])

        if in_newitem_vars.difference(in_table_vars):
            variable_change = True

        # if either one changed then we update the item
        if date_range_change | variable_change:
            if response["Item"]["dataset_start"] > db_item["start_date"]:
                item["dataset_start"] = db_item["start_date"]
            elif response["Item"]["dataset_end"] < db_item["end_date"]:
                item["dataset_end"] = db_item["end_date"]

            if variable_change:
                in_table_vars = in_table_vars.union(in_newitem_vars)
                item["variables"] = in_table_vars

            # change the modification date for the item - this will alert any subscribers to the data product
            item["dataset_update"] = dt.now().isoformat()

            # put the new item back in to the table
            summary_table.put_item(Item=item)

    else:
        # item is not in the table so register the data
        db_item_summary = {
            "mission": db_item["mission"],
            "dataset": db_item["dataset"],
            "dataset_start": db_item["start_date"],
            "dataset_end": db_item["end_date"],
            "instrument": db_item["instrument"],
            "variables": in_newitem_vars,
            "dataset_update": db_item["dataset_update"],
        }
        summary_table.put_item(Item=db_item_summary)


def lambda_handler(event, context):
    obj, vars = retrieve_object(event["file_meta"])
    register_item(obj)
    update_summary_table(obj, vars)
