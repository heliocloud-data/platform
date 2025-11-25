[![Coverage](https://gitlab.smce.nasa.gov/heliocloud/platform/badges/develop/coverage.svg)](https://gitlab.smce.nasa.gov/api/v4/projects/139/jobs/artifacts/develop/download?job=coverage)
[![pylint](https://gitlab.smce.nasa.gov/heliocloud/platform/-/jobs/artifacts/develop/raw/public/pylint.svg?job=static-analysis)](https://gitlab.smce.nasa.gov/api/v4/projects/139/jobs/artifacts/develop/raw/pylint.txt?job=static-analysis)

# HelioCloud

- [Overview](#overview)
- [Commits](#commits)

+ [Deployment](documentation/INSTALL.md)
+ [Testing](documentation/TESTING.md)
+ [FAQ](documentation/FAQ.md)


## Overview
This repository contains the core codebase, installer and associated tools for instantiating and managing a HelioCloud
instance in AWS. 

The HelioCloud instantiation process is implemented as an AWS CDK project that - when provided an instance configuration 
pulls in the necessary CDK Stack definitions and instantiates/updates a HelioCloud instance in a configured AWS account.

For Daskhub specific cost monitoring, see [Daskhub Cost Monitoring with Kubecost](./daskhub/COST_MONITORING.md).

For general HelioCloud cost information, see presentations/posters with cost related information:
- [HelioCloud: Collaborative Computing and Cost Management via Commercial Cloud](https://zenodo.org/records/14918634)
- [Pop-up Cloud-Based Jupyter Platforms for Coding Camps Using HelioCloud](https://zenodo.org/records/14918031)

Deploying a HelioCloud instance is a simple matter of ensuring your local and AWS environments support the installation, 
setting a few configuration options to fine tune your deployment to your needs, running the CDK application and finally
doing a few quick checks to confirm your HelioCloud instance is operating correctly. 


## Commits
### Prepping your changes as a pull or merge request

*The following is performed automatically by `pre-commit`.*

After completing and testing your changes, you will want to take some additional steps to maximize
the potential that the pull or merge request you put together is accepted. We recommend you:
- Run `black` to format all of your changes in keeping with HelioCloud's code formatting conventions
```shell
black .
```
- Run `pylint` to conduct a static code analysis of the codebase and see if you introduced any errors,
deviations from coding standards, etc. 
```shell
pylint *
```

Provided you get clean feedback from black & pylint and your tests pass, you should feel
pretty comfortable any merge request you post would get rejected for not adhering to the 
codebase conventions.
