"""
Defines the EC2 host profiles that will be displayed and made available for instantiation
in the Portal.
"""

import os

instance_types_master_dict = {
    "General Purpose": {
        "description": "General purpose instances provide a balance of compute, memory and networking resources, and can be used for a variety of diverse workloads. These instances are ideal for applications that use these resources in equal proportions such as web servers and code repositories.",
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
        "description": "Compute Optimized instances are ideal for compute bound applications that benefit from high performance processors. Instances belonging to this family are well suited for batch processing workloads, media transcoding, high performance web servers, high performance computing (HPC), scientific modeling, dedicated gaming servers and ad server engines, machine learning inference and other compute intensive applications.",
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
        "description": "Memory optimized instances are designed to deliver fast performance for workloads that process large data sets in memory.",
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
        "description": "Accelerated computing instances use hardware accelerators, or co-processors, to perform functions, such as floating point number calculations, graphics processing, or data pattern matching, more efficiently than is possible in software running on CPUs.",
        "types": [
            "g4dn.xlarge",
            "g4dn.2xlarge",
            "g4dn.4xlarge",
            "g4dn.8xlarge",
            "g4dn.16xlarge",
            "g4dn.12xlarge",
            "g4dn.metal",
        ],
    },
}

image_id_dict = {
    "us-east-1": {
        "Amazon Linux": ["ami-0cff7528ff583bf9a", "ami-031118784a2fe4935"],
        "Ubuntu": ["ami-052efd3df9dad4825", "ami-077fb40eebcc23898"],
        "Red Hat": ["ami-06640050dc3f556bb"],
    },
    "us-east-2": {
        "Amazon Linux": ["ami-02d1e544b84bf7502", "ami-08763b23164088ec6"],
        "Ubuntu": ["ami-02f3416038bdb17fb", "ami-0e8db731b7900e255"],
        "Red Hat": ["ami-092b43193629811af"],
    },
}

security_group_id = os.getenv("DEFAULT_SECURITY_GROUP_ID")
default_ec2_instance_profile_arn = os.getenv("DEFAULT_EC2_INSTANCE_PROFILE_ARN")
default_subnet_id = os.getenv("DEFAULT_EC2_SUBNET_ID")
