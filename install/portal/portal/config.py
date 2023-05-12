import os

### site config
site_url = os.getenv('SITE_URL')

### aws config
region = os.getenv('REGION')

### cognito config
app_name = os.getenv('APP_NAME')
aws_cognito_domain = f'https://{app_name}.auth.{region}.amazoncognito.com'
with open('/run/secrets/identity_pool_id') as f:
    identity_pool_id = f.read()
with open('/run/secrets/user_pool_client_secret') as f:
    user_pool_client_secret = f.read()
with open('/run/secrets/user_pool_client_id') as f:
    user_pool_client_id = f.read()
user_pool_id = os.getenv('USER_POOL_ID')
redirect_url = f'{site_url}/loggedin'

### flask config
with open('/run/secrets/flask_secret_key') as f:
    flask_secret_key = f.read()

