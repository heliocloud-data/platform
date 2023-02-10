This folder contains the CDK stack definition for setting up the base data environment of a HelioCloud instance, consisting of:
- public S3 bucket creation with appropriate permissions for "requestor pays" access
- Lambdas for managing file registry within the public s3 bucket
- A file registry server that HelioCloud instances (including this and external ones) can query for information on datasets stored within this instance
- A HelioCloud registration process, responsible for registering this HelioCloud instance in the central registrar (GitHub) for other clouds to be aware of
