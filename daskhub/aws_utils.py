def get_instance_types_by_region(region_name):
    import boto3

    ec2_client = boto3.client("ec2", region_name=region_name)
    instance_types = set()
    describe_args = {}

    print(f"Fetching supported instance types for region {region_name} ...")
    while True:
        describe_result = ec2_client.describe_instance_types(**describe_args)
        for i in describe_result["InstanceTypes"]:
            instance_types.add(i["InstanceType"])

        if "NextToken" not in describe_result:
            break
        describe_args["NextToken"] = describe_result["NextToken"]

    return instance_types
