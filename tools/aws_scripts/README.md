# AWS Client Scripts for HelioCloud

## About

These are scripts for maintaining HelioCloud infrastructure in AWS 

## Requirements

You need to be able to run the AWS client and BASH shell scripts. You will also need to have administrative priviledges on the AWS instance.

## Setup

You will need to generate an AWS key and cache the key and passphrase in ~/.aws/credentials. Its useful to also put in the region of your instance in this file as well.

## Usage

FIRST: You will need to use the aws-mfa script first before any of the others. It provides several enviroment variables, including a session token. Once you have done this, the other scripts will work. 
