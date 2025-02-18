"""
Defines the EC2 host profiles that will be displayed and made available for instantiation
in the Portal.
"""

import os

instance_types_master_dict = {
    "General Purpose": {
        "description": "General purpose instances provide a balance of compute, memory and "
        "networking resources, and can be used for a variety of diverse workloads. "
        "These instances are ideal for applications that use these resources in "
        "equal proportions such as web servers and code repositories.",
        "types": [
            "t2.nano",
            "t2.micro",
            "t2.small",
            "t2.medium",
            "m5.large",
            "m5.xlarge",
            "m5.2xlarge",
            "m5.4xlarge",
        ],
    },
    "Compute Optimized": {
        "description": "Compute Optimized instances are ideal for compute bound applications that "
        "benefit from high performance processors. "
        "Instances belonging to this family are well suited for batch processing "
        "workloads, media transcoding, high performance web servers, "
        "high performance computing (HPC), scientific modeling, "
        "dedicated gaming servers and ad server engines, "
        "machine learning inference and other compute intensive applications.",
        "types": [
            "c5.large",
            "c5.xlarge",
            "c5.2xlarge",
            "c5.4xlarge",
            "c5.9xlarge",
            "c5.12xlarge",
            "c5.18xlarge",
            "c5.24xlarge",
            "c5.metal",
        ],
    },
    "Memory Optimized": {
        "description": "Memory optimized instances are designed to deliver fast performance for "
        "workloads that process large data sets in memory.",
        "types": [
            "r5.large",
            "r5.xlarge",
            "r5.2xlarge",
            "r5.4xlarge",
            "r5.8xlarge",
            "r5.12xlarge",
            "r5.16xlarge",
            "r5.24xlarge",
            "r5.metal",
        ],
    },
    "Accelerated Compute": {
        "description": "Accelerated computing instances use hardware accelerators, "
        "or co-processors, to perform functions, such as floating point number "
        "calculations, graphics processing, or data pattern matching, more "
        "efficiently than is possible in software running on CPUs.",
        "types": [
            "g4dn.xlarge",
            "g4dn.2xlarge",
            "g4dn.4xlarge",
            "g4dn.8xlarge",
            "g4dn.16xlarge",
            "g4dn.12xlarge",
        ],
    },
}

image_id_dict = {
    "us-east-1": {
        "Amazon Linux": ["ami-04681163a08179f28", "ami-0829b2f2bd222cfe8"],
        "Ubuntu": ["ami-0e1bed4f06a3b463d", "ami-0271ce88f6c03e149"],
        "Red Hat": ["ami-030ea610f78de23e1"],
    },
    "us-east-2": {
        "Amazon Linux": ["ami-07f463d9d4a6f005f", "ami-08c22a9354a08c273"],
        "Ubuntu": ["ami-0884d2865dbe9de4b", "ami-0ce21b0ce8e0f5a37"],
        "Red Hat": ["ami-05345ce5eb2f71fbf"],
    },
    "us-west-1": {
        "Amazon Linux": ["ami-03392a27e4a01f1e4", "ami-01d659ac1b22ecd3d"],
        "Ubuntu": ["ami-0d413c682033e11fd", "ami-030896954b2b72361"],
        "Red Hat": ["ami-0828b3db63cd8906d"],
    },
    "us-west-2": {
        "Amazon Linux": ["ami-000089c8d02060104", "ami-03ee247e7331b5439"],
        "Ubuntu": ["ami-0606dd43116f5ed57", "ami-0a2b85e15b7c0ac34"],
        "Red Hat": ["ami-0cb6ed781c51d120d"],
    },
}

security_group_id = os.getenv("DEFAULT_SECURITY_GROUP_ID")
default_ec2_instance_profile_arn = os.getenv("DEFAULT_EC2_INSTANCE_PROFILE_ARN")
default_subnet_id = os.getenv("DEFAULT_EC2_SUBNET_ID")
