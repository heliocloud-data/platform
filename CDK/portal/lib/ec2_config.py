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
        "Amazon Linux": ["ami-053a45fff0a704a47", "ami-08746e53f6439b6b6"],
        "Ubuntu": ["ami-0609a4e88e9e5a526", "ami-0ea895ddeb71d5222"],
        "Red Hat": ["ami-0fb13bb53494158e9"],
    },
    "us-east-2": {
        "Amazon Linux": ["ami-0604f27d956d83a4d", "ami-07ed1d25d28b727a4"],
        "Ubuntu": ["ami-0b764103c341230da", "ami-020d8846a7a4c8d22"],
        "Red Hat": ["ami-0aeea2f24f6d3ba32"],
    },
    "us-west-1": {
        "Amazon Linux": ["ami-0e443b903466f6804", "ami-0398f3b7705a87b9f"],
        "Ubuntu": ["ami-041bf99d36575b514", "ami-0ae897b08e9b4ae98"],
        "Red Hat": ["ami-068c2af1200ef7356"],
    },
    "us-west-2": {
        "Amazon Linux": ["ami-09245d5773578a1d6", "ami-025c55292f44ac872"],
        "Ubuntu": ["ami-0de5ce2b7cd70d035", "ami-057ac5144e85b2e52"],
        "Red Hat": ["ami-0367f2b5c3d1ef960"],
    },
}

security_group_id = os.getenv("DEFAULT_SECURITY_GROUP_ID")
default_ec2_instance_profile_arn = os.getenv("DEFAULT_EC2_INSTANCE_PROFILE_ARN")
default_subnet_id = os.getenv("DEFAULT_EC2_SUBNET_ID")
