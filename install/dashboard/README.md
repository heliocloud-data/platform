# HelioCloud Dashboard

This repository holds code to launch the user dashboard component of HelioCloud.
It uses `flask` as the backend framework and is hosted as an EC2 Load balancer.
Deployment on AWS is through Docker using their cloud connectivity capability.


### File structure
```
dashboard-flask
│   README.md
│   docker-compose.yml    
└───dashboard
│   │   app.py
│   │   auth.py
│   │   aws.py
│   │   ec2.py
│   │   config.py
│   │   ec2_config.py
│   │   Dockerfile
│   │   requirements.txt
│   └───static
│       │   assets
│       │   css
│       │   js
│   └───templates
│       │   ...
└───secrets
│   │   flask_secret_key.txt
│   │   identity_pool_id.txt
│   │   user_pool_client_id.txt
│   │   user_pool_client_secret.txt
└───deploy
    │   deployment_instructions.md
    │   ...
```

#### For docker configuration:
- `dashboard-flask/docker-compose.yml`
- `dashboard-flask/dashboard/Dockerfile`
- `dashboard-flask/dashboard/requirements.txt`
#### For dashboard build: `dashboard-flask/dashboard`
- `app.py` - backend code
- `aws.py` - boto3 calls to AWS
- `ec2.py` - boto3 calls to AWS exclusively for EC2
- `auth.py` - code for user authentication
- `ec2_config.py` - configurations for EC2 instances
- `config.py` - general configurations for dashboard code
- `static/` - contains CSS files for html layout
- `templates/` - contains HTML files for pages of dashboard
#### For housing secrets in Docker: `dashboard-flask/secrets`
- files used by Docker to keep secrets
#### For deployment instructions: `deploy`
- files used by Docker to keep secrets

### Deployment

More detailed instructions are in `dashboard-flask/deploy/deployment_instructions.md`. Summary of steps:
1. Create Cognito user pool and identity pool.
2. Create and push up local image to ECR.
4. Deploy on ECS.
5. Connect to URL.