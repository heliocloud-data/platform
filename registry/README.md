##### HelioCloud Registry Service

The HelioCloud Registry Service enables the storage and registration of HelioPhysics data sets within a HelioCloud instance. Installation prepares a public AWS S3 bucket for data set storage, and configures a combination of AWS Lambdas, DynamoDB to act as the file registry pipeline and database. A HAPI-like REST service is deployed as the interface to the registry - enabling internal & external processes (e.g. Jupyter Notebooks in this HelioCloud instance, or others) to inquire as to what datasets are stored in this particular HelioCloud instance.


The **previous** sub directory contains the initial set of AWS Lambda scripts and DynamoDB setup used to register a set of MMS files in S3. It is actively being picked apart to determine what code will be reused in developing the file registry.


