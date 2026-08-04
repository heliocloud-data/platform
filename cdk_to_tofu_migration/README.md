Migration from CDK to OpenTofu HelioCloud Platform Deployment


Plan Draft #1


i am currently writing a github actions workflow to;

1. use an opentofu data resource (or a local call within the child module main.tf file)  to read all cloudformation/cdk-stacks names related to the specific environment (in this case our test env), and export those stack names to the next step.
2. using a bash script, make an aws-cli call aws cloudformation describe-stack-resources --stack-name YOUR_CDK_STACK_NAME and output and save the response to a .json file. Do this for each stack.
3. Next, save the json files for parsing.
4. If The next github actions workflow job would be to call an AI coding agent for opentofu that reads the exported resource ids/names from the json file in the previous step..
5. Next is the same process but the AI agent reads the current opentofu configuration of your local directory and remote states/statefiles (if some resources have already been stood up/imported) of the environment.
6. using the data collected from the previous two steps, use the AI agent to create the import.tf file needed for importing cdk resources into the opentofu deployment configuration using the import {} block. .
7. Next would be to run a job to lint/fmt/validate the opentofu code.
8. Next is to ask the AI agent to map the cdk/cloudformation resources in the json file, to their opentofu resources/modules as currently deployed in the specific branch/environment.tofu plan -generate-config-out=generated_resources.tf - this script should (in theory) write out the actual import {} blocks for us.
9. finally, the last github action for this whole process creates and saves the output of tofu plan ... to a file reviewable by all team members. actual execution of tofu apply is tbd...

the saving grace of this (if it works as desired) it saves us the time of correctly matching the aws-cdk created resources to the current opentofu configuration and modules ya'll have created and pushed to develop-tf.  the most time consuming part of importing any existing resources, is to find the correct resource call for the import {} block without altering the state.

scan outputs > map resources > create import {}
