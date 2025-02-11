# -- FILE: features/portal_ec2_launch.feature

@Portal @AllInstanceTypes @slow
Feature: Log into portal and launch an EC2 instance

  Scenario:  Create a user account to run this suite of tests.
    Given a fully deployed instance of HelioCloud
     Then create a user with the name "helioptile"

  Scenario:  Attempt to access the portal site
    Given a fully deployed instance of HelioCloud
     Then go to the "portal-login-page"
      And verify the "portal-login-page"
      And enter "helioptile" in the "username" field
      And enter the password in the "password" field
      And click "Sign in"
      And verify the "portal-main-page"

  Scenario:  Create an ssh-key pair
    Given a fully deployed instance of HelioCloud
      And the user is logged in
      And no existing keypair named "the-key-to-my-heart" exists
      And no existing sshkey named "the-key-to-my-heart.pem" exists
     Then go to the "portal-keypairs-page"
      And verify the "portal-keypairs-page"
      And enter "the-key-to-my-heart" in the "key-pair-name" field
      And click "Create Key Pair"
      And click "Download Keypair File"
      And confirm file "the-key-to-my-heart.pem" exists in the Downloads directory

  Scenario Outline:  Launch an EC2 instance (instance_type: <instance_type>)
    Given a fully deployed instance of HelioCloud
      And the user is logged in
      And no existing ec2 instance named "<instance_name>" exists
     Then go to the "portal-launch_instance-page"
      And verify the "portal-launch_instance-page"
      And click "<img_os_tab>"
       And click "<ami_name>"
      And click "<instance_type_group>"
       And click "<instance_type>"
      And select "the-key-to-my-heart" in the "Select Key Pair" dropdown
      And enter "<volume_size_in_gb>" in the "Volume Size (GB)" field
      And enter "<instance_name>" in the "Instance Name" field
      And click "Launch Instance"
      And wait 2 seconds
      And delete ec2 instance named "<instance_name>"

    Examples:
      | instance_name                    | instance_type_group | instance_type | img_os_tab   |         ami_name                                               | volume_size_in_gb |
      | helioptile-ec2-instance-type-001 | General Purpose     | t2.nano       | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-002 | General Purpose     | t2.micro      | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-003 | General Purpose     | t2.small      | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-004 | General Purpose     | t2.medium     | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-005 | General Purpose     | m5.large      | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-006 | General Purpose     | m5.xlarge     | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-007 | General Purpose     | m5.2xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-008 | General Purpose     | m5.4xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-009 | Compute Optimized   | c5.large      | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-010 | Compute Optimized   | c5.xlarge     | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-011 | Compute Optimized   | c5.2xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-012 | Compute Optimized   | c5.4xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-013 | Compute Optimized   | c5.9xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-014 | Compute Optimized   | c5.12xlarge   | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-015 | Compute Optimized   | c5.18xlarge   | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-016 | Compute Optimized   | c5.24xlarge   | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-017 | Compute Optimized   | c5.metal      | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-018 | Memory Optimized    | r5.large      | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-019 | Memory Optimized    | r5.xlarge     | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-020 | Memory Optimized    | r5.2xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-021 | Memory Optimized    | r5.4xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-022 | Memory Optimized    | r5.8xlarge    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-023 | Memory Optimized    | r5.12xlarge   | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-024 | Memory Optimized    | r5.16xlarge   | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-025 | Memory Optimized    | r5.24xlarge   | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-026 | Memory Optimized    | r5.metal      | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-027 | Accelerated Compute | g4dn.xlarge   | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-028 | Accelerated Compute | g4dn.2xlarge  | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-029 | Accelerated Compute | g4dn.4xlarge  | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-030 | Accelerated Compute | g4dn.8xlarge  | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-031 | Accelerated Compute | g4dn.16xlarge | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-032 | Accelerated Compute | g4dn.12xlarge | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |
      | helioptile-ec2-instance-type-033 | Accelerated Compute | g4dn.metal    | Amazon Linux | amzn2-ami-kernel-5.10-hvm-2.0.20250201.0-x86_64-gp2            |                 9 |


  @Cleanup
  Scenario:  Remove all AWS resources generated by this test
    Given a fully deployed instance of HelioCloud
      And no existing keypair named "the-key-to-my-heart" exists
      And no existing ec2 instance named "helioptile-ec2-001" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-001" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-002" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-003" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-004" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-005" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-006" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-007" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-008" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-009" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-010" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-011" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-012" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-013" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-014" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-015" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-016" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-017" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-018" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-019" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-020" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-021" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-022" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-023" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-024" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-025" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-026" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-027" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-028" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-029" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-030" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-031" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-032" exists
      And no existing ec2 instance named "helioptile-ec2-instance-type-033" exists

  @Cleanup
  Scenario:  Delete the user account that ran with this suite of tests.
    Given a fully deployed instance of HelioCloud
     Then delete a user with the name "helioptile"
