
import boto3

# get our list of files/s3 objects
def list_objects(bucket_name:str, list_all_objects:bool=False)->list:  

    # declare and open up bucket
    s3_res = boto3.resource('s3')
    s3_bucket = s3_res.Bucket(bucket_name)

    s3_objs = []
    if list_all_objects:
        for obj in s3_bucket.object_versions.all():
            obj_id = obj.id
            if obj.id is None or obj.id == 'null':
                obj_id = ""
            s3_objs.append([obj.key, obj.id])
            #s3_objs.append({obj.key, obj.version})
    else:
        for obj in s3_bucket.objects.all():
            s3_objs.append([obj.key, ""])

    return s3_objs


if __name__ == '__main__':  # use if csv of text
    import argparse

    ap = argparse.ArgumentParser(description='Client to pull list of objects in an s3 bucket.')

    ap.add_argument('-a', '--all_versions', default = False, action = 'store_true', help='Pull data for all objects.')
    ap.add_argument('-b', '--bucket_name', type=str, help='Name of S3 bucket to get objects for.', required=True)
    ap.add_argument('-o', '--output_filename', type=str, default="s3_objects.csv", help='Name of output filename to write reported objects to.', required=False)

    args = ap.parse_args()

    s3_objs = list_objects(args.bucket_name, args.all_versions)

    # write / cache files to local listing (speed purposes)
    with open (args.output_filename, 'w') as f:
        for s3_obj in s3_objs:
            f.write(f"{s3_obj[0]}, {s3_obj[1]}\n")

    print(f"Finished, wrote report to {args.output_filename}")




