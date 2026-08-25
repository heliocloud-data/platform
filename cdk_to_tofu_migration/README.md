Migration from CDK to OpenTofu | HelioCloud Platform Deployment

Plan Draft #2

Environment details:

- hsdcloud-testing
- us-east-2
- smdc-aws-helio2 (320962816401)

Find all currently deployed AWS CDK/Cloudformation resources for the HelioCloud Platform hsdcloud-testing environment.

1. Use the AWS CLI to list all Cloudformation Stacks (by StackName) deployed to the hsdcloud-testing environment. Save the output to local files in json format for use in the next step.

   For all initial core stacks in Platform, run:

   `aws cloudformation describe-stacks --query "Stacks[?contains(StackName,'hsdcloudtesting')].StackName" > stack_names.json`

   For all eks-related stacks created during the Daskhub deployment, run:

   `aws cloudformation describe-stacks --query "Stacks[?contains(StackName,'hsdcloud-test')].StackName" > eks_stacks_names.json`
2. Use python script to list all AWS resources created by the CDK deployment. Save each output to a json file for parsing.

   `python3 get_cfn_resources.py`

<!-- use an opentofu data resource (or a local call within the child module main.tf file)  to read all cloudformation/cdk-stacks names related to the specific environment (in this case our test env), and export those stack names to the next step.

using a bash script, make an aws-cli call aws cloudformation describe-stack-resources --stack-name YOUR_CDK_STACK_NAME and output and save the response to a .json file. Do this for each stack.

Next, save the json files for parsing.

If The next github actions workflow job would be to call an AI coding agent for opentofu that reads the exported resource ids/names from the json file in the previous step..

Next is the same process but the AI agent reads the current opentofu configuration of your local directory and remote states/statefiles (if some resources have already been stood up/imported) of the environment.

using the data collected from the previous two steps, use the AI agent to create the import.tf file needed for importing cdk resources into the opentofu deployment configuration using the import {} block. .

Next would be to run a job to lint/fmt/validate the opentofu code.

Next is to ask the AI agent to map the cdk/cloudformation resources in the json file, to their opentofu resources/modules as currently deployed in the specific branch/environment.tofu plan -generate-config-out=generated_resources.tf - this script should (in theory) write out the actual import {} blocks for us.

finally, the last github action for this whole process creates and saves the output of tofu plan ... to a file reviewable by all team members. actual execution of tofu apply is tbd...

the saving grace of this (if it works as desired) it saves us the time of correctly matching the aws-cdk created resources to the current opentofu configuration and modules ya'll have created and pushed to develop-tf.  the most time consuming part of importing any existing resources, is to find the correct resource call for the import {} block without altering the state.

scan outputs > map resources > create import {} -->
