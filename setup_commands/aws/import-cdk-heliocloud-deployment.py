import boto3
import re

CLOUDFORMATION_API_SCAN_ENABLED = True
VPC_API_SCAN_ENABLED = True
EFS_API_SCAN_ENABLED = True

# TODO  Add command-line argument
region_name='us-west-1'
session = boto3.Session(
    region_name=region_name
)

# TODO  Add command-line argument
instance_name="testing-develop"
# TODO  Add command-line argument
eks_cluster_name="eks-helio"

dump_resources = False
debug = False

def cloudformation_namify(text):
  ret = text.replace("-", "")
  return ret

def index_tags(obj):
  tags = {}
  if 'Tags' in obj:
    for tag_item in obj['Tags']:
      tags[tag_item['Key']] = tag_item['Value']

  return tags

def print_dict(item, lead=None, trail=None):
  if lead is None:
    lead = ""
  if trail is None:
    trail = ""
  if isinstance(item, dict):
    print(f"{lead}" + "{")
    for k, v in item.items():
      if isinstance(v, dict):
        print(f"{lead} {k}: " + "{")
        print_dict(v, f"{lead}  ", ",")
        print(f"{lead} " + "},")
      elif isinstance(v, list):
        print(f"{lead} {k}: [")
        for i in v:
          print_dict(i, f"{lead}  ", ",")
        print(f"{lead} ],")
      else:
        print(f"{lead} {k}: {v},")
    print(f"{lead}" + "}" + f"{trail}")
  elif isinstance(item, list):
    for i in item:
      print_dict(i, f"{lead}", ",")

  else:
    print(f"{lead}{item}{trail}")

cf_client = session.client('cloudformation')

response = cf_client.list_stacks()

starts_with_filters = [
  cloudformation_namify(instance_name),
  f"eksctl-{eks_cluster_name}-cluster",
  f"eksctl-{eks_cluster_name}-nodegroup",
]
contains_filters = [
#   "Daskhub"
]

stacks_by_name = {}

cached_tf_resources = {}

# Scan through the stacks
for item in response['StackSummaries']:
    # Skip over any deleted stacks...
    if item['StackStatus'] in ['DELETE_COMPLETE']:
      continue
      
    stack_name = item['StackName']

    include_starts_with = len(starts_with_filters) == 0
    for filter_text in starts_with_filters:
      if stack_name.startswith(filter_text):
        include_starts_with = True
        break

    include_contains = len(contains_filters) == 0
    for filter_text in contains_filters:
      if filter_text in stack_name:
        include_contains = True
        break

    if include_starts_with and include_contains:
        if debug:
          print(f"{item['StackName']}: {item['StackId']}")
          print_dict(item)

        response2 = cf_client.describe_stacks(StackName=stack_name)
        stacks_by_name[stack_name] = response2['Stacks'][0]
        if debug:
          print_dict(response2)
          print()
          print()
          print()

# Filter list of resources to project from the CDK CloudFormation API Response to
# OpenTofu/Terraform import statements.
resources_to_project = [{
    'to': 'aws_eks_cluster.private',
    'id': eks_cluster_name,
  }, {
    'to': 'aws_iam_role.HelioCloud_EKS_ClusterRole',
    'id_fstring_eval': {
      'stack_name_contains': [f"eksctl-{eks_cluster_name}-cluster"],
      'eval': "f\"{outputs['ServiceRoleARN'].split('/')[-1]}\""
    }
  }, {
    'to': 'aws_vpc.myvpc',
    'id_fstring_eval': {
      'stack_name_contains': [f"eksctl-{eks_cluster_name}-cluster"],
      'eval': "f\"{outputs['VPC']}\""
    }
  }, {
    'to': 'aws_subnet.subnet_public_01',
    'id_fstring_eval': {
      'stack_name_contains': [f"eksctl-{eks_cluster_name}-cluster"],
      'eval': "f\"{outputs['SubnetsPublic'].split(',')[0]}\""
    }
  }, {
    'to': 'aws_subnet.subnet_public_02',
    'id_fstring_eval': {
      'stack_name_contains': [f"eksctl-{eks_cluster_name}-cluster"],
      'eval': "f\"{outputs['SubnetsPublic'].split(',')[1]}\""
    }
  }, {
    'to': 'aws_eks_node_group.mng_daskhub_service',
    'id_fstring_eval': {
      'stack_name_contains': ["ng-daskhub-services"],
      'eval': "f\"{tags['alpha.eksctl.io/cluster-name']}:{tags['alpha.eksctl.io/nodegroup-name']}\""
    }
  },{
    'to': 'module.heliocloud_eks_node_group_jupyterhub_burst_compute.aws_eks_node_group.mng_jupyterhub_burst_compute',
    'id_fstring_eval': {
      'stack_name_contains': ["nodegroup-mng-burst-compute-spot"],
      'eval': "f\"{tags['alpha.eksctl.io/cluster-name']}:{tags['alpha.eksctl.io/nodegroup-name']}\""
    }
  },{
    'to': 'module.heliocloud_eks_node_group_jupyterhub_burst_compute.aws_eks_node_group.mng_jupyterhub_burst_compute_gpu_xlarge',
    'id_fstring_eval': {
      'stack_name_contains': ["nodegroup-mng-burst-compute-spot-gpu-xlarge"],
      'eval': "f\"{tags['alpha.eksctl.io/cluster-name']}:{tags['alpha.eksctl.io/nodegroup-name']}\""
    }
  },{
    'to': 'module.heliocloud_eks_node_group_jupyterhub_user_compute.aws_eks_node_group.mng_jupyterhub_user_compute',
    'id_fstring_eval': {
      'stack_name_contains': ["nodegroup-mng-user-compute"],
      'eval': "f\"{tags['alpha.eksctl.io/cluster-name']}:{tags['alpha.eksctl.io/nodegroup-name']}\""
    }
  },{
    'to': 'module.heliocloud_eks_node_group_jupyterhub_user_compute.aws_eks_node_group.mng_jupyterhub_user_compute_big',
    'id_fstring_eval': {
      'stack_name_contains': ["nodegroup-mng-user-compute-big"],
      'eval': "f\"{tags['alpha.eksctl.io/cluster-name']}:{tags['alpha.eksctl.io/nodegroup-name']}\""
    }
  },{
    'to': 'module.heliocloud_eks_node_group_jupyterhub_user_compute.aws_eks_node_group.mng_jupyterhub_user_compute_gpu_2xlarge',
    'id_fstring_eval': {
      'stack_name_contains': ["nodegroup-mng-user-gpu-2xlarge"],
      'eval': "f\"{tags['alpha.eksctl.io/cluster-name']}:{tags['alpha.eksctl.io/nodegroup-name']}\""
    }
  },{
    'to': 'module.heliocloud_auth.aws_cognito_user_pool.user_pool',
    'id_fstring_eval': {
      'stack_name_contains': ["Auth"],
      'eval': "f\"{outputs['CognitoUserPoolId']}\""
    }
  },{
    'to': 'module.heliocloud_auth.aws_cognito_user_pool_client.client',
    'id_fstring_eval': {
      'stack_name_contains': ["Auth"],
      'eval': "f\"{outputs['CognitoUserPoolId']}/{outputs['CognitoClientId']}\""
    }
  },{
    'to': 'module.heliocloud_auth.aws_cognito_user_pool_domain.domain',
    'id_fstring_eval': {
      'stack_name_contains': ["Auth"],
      'eval': "f\"{outputs['CognitoDomainPrefix']}\""
    }
  },{
    'to': 'module.heliocloud_portal.aws_cognito_identity_pool.HelioCloud_Portal_IdentityPool',
    'id_fstring_eval': {
      'stack_name_contains': ["Portal"],
      'eval': "f\"{outputs['PortalIdentityPool']}\""
    }
  },{
    'to': 'aws_kms_key.HelioCloud_eks_secrets',
    'id_fstring_eval': {
      'stack_name_contains': ["Daskhub"],
      'eval': "f\"{outputs['KMSArn']}\""
    }
  },{
    'to': 'module.efs.aws_efs_file_system.this[0]',
    'id_fstring_eval': {
      'stack_name_contains': ["Daskhub"],
      'eval': "f\"{outputs['EFSId']}\""
    }
  }
]

security_group_descriptions_to_tf_resource = {
  f"{instance_name}/Portal/PortalEc2SecurityGroup": "module.heliocloud_portal.aws_security_group.HelioCloud_Portal_UserSecurityGroup",
  f"{instance_name}/Daskhub/DaskhubEFS/EfsSecurityGroup": "module.efs.aws_security_group.this[0]"
}

if CLOUDFORMATION_API_SCAN_ENABLED:
  print("################################################################################")
  print("# Captured CloudFormation outputs")
  print("################################################################################")
  for resource_to_project in resources_to_project:
    tf_id = None
    if 'id' in resource_to_project:
      tf_id = resource_to_project['id']
    elif 'id_fstring_eval' in resource_to_project:
      stack = None

      for stack_name, item in stacks_by_name.items():
        if stack is not None:
          break


        include_contains = len(resource_to_project['id_fstring_eval']['stack_name_contains']) == 0
        for filter_text in resource_to_project['id_fstring_eval']['stack_name_contains']:
          if filter_text in stack_name:
            include_contains = True
            break

        if include_contains:
          stack = item

      if stack is None:
        print("# error: Unable to locate stack for {resource_to_project}")
        continue

      tags = index_tags(stack)

      outputs = {}
      if 'Outputs' in stack:
        for output_item in stack['Outputs']:
          outputs[output_item['OutputKey']] = output_item['OutputValue']

      tf_id = eval( resource_to_project['id_fstring_eval']['eval'])
    else:
      print(f"# error: Unable to id for {resource_to_project}")
      continue

    print("import {")
    print(f"  to = {resource_to_project['to']}")
    if tf_id is None:
      print(f"  # error: Failed to identify from CloudFormation Outputs")
      if 'id_fstring_eval' in resource_to_project:
        print(f"  # error: resource_to_project['id_fstring_eval']['eval']: {resource_to_project['id_fstring_eval']['eval']}")
        print("  # error: tags:")
        print_dict(tags, "  # error:     ")
        print("  # error: outputs:")
        print_dict(outputs, "  # error:     ")
    else:
      print(f"  id = \"{tf_id}\"")
      cached_tf_resources[resource_to_project['to']] = tf_id
    print("}")
    print()
  print()

if VPC_API_SCAN_ENABLED:
  print("################################################################################")
  print("# Captured CDK tagged VPC resources")
  print("################################################################################")
  ec2_client = session.client('ec2')
  response = ec2_client.describe_vpcs()

  # Find the VPC of the portal stack.
  portal_vpc = None
  for vpc in response['Vpcs']:
    tags = index_tags(vpc)
    if 'aws:cloudformation:stack-name' in tags:
      stack_name = tags['aws:cloudformation:stack-name']

      if cloudformation_namify(instance_name) in stack_name and 'Base' in stack_name:
        portal_vpc = vpc
        break

  if portal_vpc is not None:
    print("import {")
    print(f"  to = module.heliocloud_portal.aws_vpc.HelioCloud_Portal_VPC")
    print(f"  id = \"{portal_vpc['VpcId']}\"")
    cached_tf_resources['module.heliocloud_portal.aws_vpc.HelioCloud_Portal_VPC'] = portal_vpc['VpcId']
    print("}")
    print()

    # Describe Internet Gateways filtered by VPC ID
    response = ec2_client.describe_internet_gateways(
        Filters=[
            {'Name': 'attachment.vpc-id', 'Values': [portal_vpc['VpcId']]}
        ]
    )

    # Extract Internet Gateway IDs
    igw_ids = [igw['InternetGatewayId'] for igw in response['InternetGateways']]
    if len(igw_ids) > 0:
      print("import {")
      print(f"  to = module.heliocloud_portal.aws_internet_gateway.HelioCloud_Portal_InternetGateway")
      print(f"  id = \"{igw_ids[0]}\"")
      cached_tf_resources['module.heliocloud_portal.aws_internet_gateway.HelioCloud_Portal_InternetGateway'] = igw_ids[0]
      print("}")
      print()

    # Retrieve subnets for the given VPC
    response = ec2_client.describe_subnets(
      Filters=[
          {'Name': 'vpc-id', 'Values': [portal_vpc['VpcId']]}
      ]
    )
    subnet_idx = 0
    for subnet in response['Subnets']:
      tags = index_tags(subnet)
      if 'aws-cdk:subnet-type' in tags and tags['aws-cdk:subnet-type'] == 'Public':

        logical_id = tags['aws:cloudformation:logical-id']
        m = re.search("PublicSubnet([0-9]+)", logical_id)
        subnet_idx = int(m.group(1))

        # HelioCloudVPCPublicSubnet2Subnet
        print("import {")
        if dump_resources:
          print("#  Subnet")
          print_dict(subnet, "#   ")
        print(f"  to = module.heliocloud_portal.aws_subnet.HelioCloud_Portal_Subnet_Public_0{subnet_idx}")
        print(f"  id = \"{subnet['SubnetId']}\"")
        cached_tf_resources[f"module.heliocloud_portal.aws_subnet.HelioCloud_Portal_Subnet_Public_0{subnet_idx}"] = subnet['SubnetId']
        print("}")
        print()

        if debug:
          print_dict(subnet)
        subnet_idx = subnet_idx + 1

    response = ec2_client.describe_security_groups(
      MaxResults=100,
      Filters=[
          {'Name': 'vpc-id', 'Values': [portal_vpc['VpcId']]}
      ]
    )

    for sg in response['SecurityGroups']:
      if debug:
        print_dict(sg)

      if sg['Description'] in security_group_descriptions_to_tf_resource:
        to = security_group_descriptions_to_tf_resource[sg['Description']]
        print("import {")
        if dump_resources:
          print("#  Security Group")
          print_dict(sg, "#   ")
        print(f"  to = {to}")
        print(f"  id = \"{sg['GroupId']}\"")
        cached_tf_resources[to] = sg['GroupId']
        print("}")
        print()
      

if EFS_API_SCAN_ENABLED:
  print("################################################################################")
  print("# Captured EFS Resources")
  print("################################################################################")
  efs_client = boto3.client("efs", region_name=region_name)

  if 'module.efs.aws_efs_file_system.this[0]' not in cached_tf_resources:
    print("# error: Unable to locate EFS File System resource")
    file_system_id = None
  else:
    file_system_id = cached_tf_resources['module.efs.aws_efs_file_system.this[0]']

  # Call AWS API to get mount targets
  if file_system_id is not None:
    response = efs_client.describe_mount_targets(FileSystemId=file_system_id)
    mount_targets = response.get("MountTargets", [])

    for mount_target in mount_targets:
      mount_target_id = mount_target['MountTargetId']
      availability_zone_name = mount_target['AvailabilityZoneName']
      print("import {")
      if dump_resources:
        print("#  EFS Mount Target")
        print_dict(mount_target, "#   ")
      print(f"  to = module.efs.aws_efs_mount_target.this[\"{availability_zone_name}\"]")
      print(f"  id = \"{mount_target_id}\"")
      cached_tf_resources[f"module.efs.aws_efs_mount_target.this[\"{availability_zone_name}\"]"] = mount_target_id
      print("}")
      print()
