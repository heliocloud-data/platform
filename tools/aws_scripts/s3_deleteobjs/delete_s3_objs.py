
# Program to delete ALL versions of an object in an S3 bucket. Takes a list of objs to be deleted.
#
import boto3
from botocore.exceptions import *

import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def permanently_delete_object(bucket, object_key)->None:
    """
    Permanently deletes a versioned object by deleting all of its versions.

    Usage is shown in the usage_demo_single_object function at the end of this module.

    :param bucket: The bucket that contains the object.
    :param object_key: The object to delete.
    """
    try:
        bucket.object_versions.filter(Prefix=object_key).delete()
        #logger.debug("Permanently deleted all versions of object %s.", object_key)
    except ClientError:
        logger.exception("Couldn't delete all versions of %s.", object_key)
        raise


def delete_files (bucket_name:str, filelist_name:str, start:int=0, end:int=-1)->None:

    # open up bucket
    s3_res = boto3.resource('s3')
    s3_bucket = s3_res.Bucket(bucket_name)

    with open (filelist_name) as f:
        s3_objs = f.read().splitlines()

    # delete each obj one by one (*sigh*)
    # implement a little counter so we can check progress
    i = 0
    for s3_obj in s3_objs[start:end]:
        try:
             permanently_delete_object(s3_bucket, s3_obj)
             if i % 10000 == 0:
                 logger.info(f"Deleted {i} objs");
             i = i + 1

        except Exception as ex:
            pass

    logger.info(f"Finished. Deleted {i} objs");


if __name__ == '__main__':
    import argparse

    # Use nargs to specify how many arguments an option should take.
    ap = argparse.ArgumentParser(description='Extract relevant text from Astro2010 whitepaper pdfs.')
    ap.add_argument('-b', '--bucket', type=str, required=True, help=f"Name of bucket to delete objects from ")
    ap.add_argument('-o', '--objlist_name', type=str, required=True, help=f"Name of file with list of objects to delete")
    ap.add_argument('-s', '--start', type=int, default=0, help=f"Start object index in list, defaults to first object")
    ap.add_argument('-e', '--end', type=int, default=-1, help=f"Stop/end object index in list, defaults to last object")
    ap.add_argument('-n', '--number', type=int, default=-1, help=f"Number of objects to delete, dont use with --end")

    # parse argv
    args = ap.parse_args()

    # check number
    if args.number > 0:
        args.end = args.start + args.number 

    delete_files(args.bucket, args.objlist_name, args.start, args.end)


