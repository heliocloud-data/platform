# HelioCloud Dashboard

This repository holds code to launch the user portal component of HelioCloud.
It uses `flask` as the backend framework and is hosted as an EC2 Load balancer and AWS calls are made using the `boto3` API.

### File structure
```
portal
│   portal_stack.py
│   README.md 
└───portal
│   │   access.py
│   │   app.py
│   │   auth.py
│   │   aws.py
│   │   config.py
│   │   ec2.py
│   │   ec2_config.py
│   │   Dockerfile
│   │   messages.py
│   │   requirements.txt
│   └───static
│       │   assets
│       │   css
│       │   js
│   └───templates
│       │   ...
```

#### For portal build: `portal/portal`
- `access.py` - boto3 calls for IAM access
- `app.py` - backend code for portal
- `auth.py` - code for user authentication
- `aws.py` - boto3 calls to AWS
- `config.py` - general configurations for dashboard code
- `ec2.py` - boto3 calls to AWS exclusively for EC2
- `ec2_config.py` - configuration for portal-created EC2 instances
- `Dockerfile` - Docker deployment file
- `messages.py` - code for producing various generated messages for the user.
- `requirements.txt` - packages required for portal deploy
- `static/` - contains CSS files for html layout
- `templates/` - contains HTML files for pages of dashboard

#### Deployment Notes
Portal deployment uses AWS CDK.
To deploy the user portal module as a part of your Heliocloud instance, make sure you set `portal: True` under `enabled` in your instance `.yaml` file.

Deployment requires Docker to be running as a part of AWS ECS set up. 
Make sure Docker[https://www.docker.com] is installed on your machine and that you are logged in. 

The user portal requires that the domain name has an active public SSL certificate for the host domain (e.g. `your-heliocloud-domain.org`), validated through Amazon Certification Manager (ACM). 
See [here](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html#:~:text=Sign%20in%20to%20the%20AWS,name%20such%20as%20example.com%20) for instructions on how to set up a public certificate through ACM. 
As a part of portal deployment configuration, add the certificate ARN to your instance `.yaml` file.