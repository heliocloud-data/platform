# -- FILE: features/portal_ec2_launch.feature

@Portal
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

  Scenario:  Launch an EC2 instance
    Given a fully deployed instance of HelioCloud
      And the user is logged in
      And no existing ec2 instance named "helioptile-ec2-001" exists
     Then go to the "portal-launch_instance-page"
      And verify the "portal-launch_instance-page"
      And click "Amazon Linux"
       And click "amzn2-ami-kernel-5.10-hvm-2.0.20220606.1-x86_64-gp2"
      And click "General Purpose"
       And click "t2.micro"
      And select "the-key-to-my-heart" in the "Select Key Pair" dropdown
      And enter "9" in the "Volume Size (GB)" field
      And enter "helioptile-ec2-001" in the "Instance Name" field
      And click "Launch Instance"

  @Cleanup
  Scenario:  Remove all AWS resources generated by this test
    Given a fully deployed instance of HelioCloud
      And no existing keypair named "the-key-to-my-heart" exists
      And no existing ec2 instance named "helioptile-ec2-001" exists

  @Cleanup
  Scenario:  Delete the user account that ran with this suite of tests.
    Given a fully deployed instance of HelioCloud
     Then delete a user with the name "helioptile"