import os

### site config
site_url = os.getenv("SITE_URL")

### aws config
region = os.getenv("REGION")

### cognito config
app_name = os.getenv("APP_NAME")
aws_cognito_domain = f"https://{app_name}.auth.{region}.amazoncognito.com"
identity_pool_id = os.getenv("IDENTITY_POOL_ID")
user_pool_client_secret = os.getenv("USER_POOL_CLIENT_SECRET")
user_pool_client_id = os.getenv("USER_POOL_CLIENT_ID")
user_pool_id = os.getenv("USER_POOL_ID")
redirect_url = f"{site_url}/loggedin"
flask_secret_key = os.getenv("FLASK_SECRET_KEY")
