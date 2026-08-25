#! /usr/bin/env python3

import json
import boto3
import sys
from botocore.exceptions import ClientError

def get_stack_resources(json_filepath):
    # Initialize the CloudFormation client
    # It will automatically use your configured AWS credentials and default region
    cf_client = boto3.client('cloudformation')
    
    # Load the stack names from the local JSON file
    try:
        with open(json_filepath, 'r') as file:
            stack_names = json.load(file)
    except FileNotFoundError:
        print(f"Error: Could not find file {json_filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File {json_filepath} is not valid JSON")
        sys.exit(1)

    # Ensure the JSON is a list of strings
    if not isinstance(stack_names, list):
        print("Error: The JSON file must contain a list of stack names.")
        sys.exit(1)

    # Initialize a paginator for listing stack resources
    paginator = cf_client.get_paginator('list_stack_resources')
    
    all_resources = {}

    for stack_name in stack_names:
        print(f"\nFetching resources for stack: {stack_name}")
        print("-" * 50)
        
        stack_resources = []
        try:
            # Paginate through all resources in the stack
            for page in paginator.paginate(StackName=stack_name):
                for resource in page.get('StackResourceSummaries', []):
                    resource_info = {
                        'LogicalId': resource.get('LogicalResourceId'),
                        'PhysicalId': resource.get('PhysicalResourceId'),
                        'Type': resource.get('ResourceType'),
                        'Status': resource.get('ResourceStatus')
                    }
                    stack_resources.append(resource_info)
                    
                    # Print the resource details to the console
                    print(f"Logical ID:  {resource_info['LogicalId']}")
                    print(f"Type:        {resource_info['Type']}")
                    print(f"Physical ID: {resource_info['PhysicalId']}")
                    print(f"Status:      {resource_info['Status']}\n")
            
            all_resources[stack_name] = stack_resources
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            print(f"Failed to fetch resources for {stack_name}: {error_message}")
            all_resources[stack_name] = {"Error": error_message}

    return all_resources

if __name__ == "__main__":
    # Specify the path to your JSON file here
    json_file = 'stack_names.json' 
    
    # Run the function
    results = get_stack_resources(json_file)
    
    # Optional: Save the results to a new JSON file
    with open('stack_resources_output.json', 'w') as outfile:
        json.dump(results, outfile, indent=4)
        print("\nResults successfully saved to stack_resources_output.json")