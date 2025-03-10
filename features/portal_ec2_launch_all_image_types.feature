# -- FILE: features/portal_ec2_launch.feature

@Portal @AllAmiTypes @slow
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

  Scenario Outline:  Launch an EC2 instance (ami_name: <ami_name>)
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
      | instance_name                 | img_os_tab   | ami_name                                                                           | instance_type_group | instance_type | volume_size_in_gb |
      | helioptile-ec2-image-type-001 | Amazon Linux | al2023-ami-2023.6.20250211.0-kernel-6.1-x86_64                                     | General Purpose     | t2.micro      |                 9 |
      | helioptile-ec2-image-type-002 | Amazon Linux | Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.5.1 (Amazon Linux 2023) 20250216 | General Purpose     | t2.micro      |                 9 |
      | helioptile-ec2-image-type-003 | Ubuntu       | ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20250214                 | General Purpose     | t2.micro      |                 9 |
      | helioptile-ec2-image-type-004 | Ubuntu       | Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.5.1 (Ubuntu 22.04) 20250216      | General Purpose     | t2.micro      |                20 |
      | helioptile-ec2-image-type-005 | Red Hat      | RHEL-9.5.0_HVM-20250128-x86_64-0-Hourly2-GP3                                       | General Purpose     | t2.micro      |                 9 |
  @Cleanup
  Scenario:  Remove all AWS resources generated by this test
    Given a fully deployed instance of HelioCloud
      And no existing keypair named "the-key-to-my-heart" exists
      And no existing ec2 instance named "helioptile-ec2-001" exists
      And no existing ec2 instance named "helioptile-ec2-image-type-001" exists
      And no existing ec2 instance named "helioptile-ec2-image-type-002" exists
      And no existing ec2 instance named "helioptile-ec2-image-type-003" exists
      And no existing ec2 instance named "helioptile-ec2-image-type-004" exists
      And no existing ec2 instance named "helioptile-ec2-image-type-005" exists

  @Cleanup
  Scenario:  Delete the user account that ran with this suite of tests.
    Given a fully deployed instance of HelioCloud
     Then delete a user with the name "helioptile"
