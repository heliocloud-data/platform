# HelioCloud tool for listing the users in the Cognito pool(s) created

aws cognito-idp list-users --user-pool-id us-east-1_p09cMJeEj | grep Username | sed s/\"//g | sed s/Username// | sed s/,// | sed s/:// | sed s/\ //g | sort
