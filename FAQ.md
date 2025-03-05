# This is an FAQ styled section to help with deploying and using Daskhub.

---

## Where to:

#### Find the Certificate ARN:

<details>
<summary>Click to expand.</summary>
You can find the certificate ARN by going to the <b><ins>AWS Certificate Manager</ins></b> through the AWS Console, then go to <b><ins>List certificates</ins></b>, then click on the appropriate name/url.
The ARN will be displayed at the top of the page with a helpful copy button.
</details><br>

#### Find the DaskHub URL:

<details>
<summary>Click to expand.</summary>
You can find the URL by going to <b><ins>Route53</ins></b> through the AWS Console, then go to <b><ins>Hosted Zones</ins></b>, then click on the appropriate name/url.
The URL(s) will be displayed at the bottom of the page, your instance name should be included in the URL.
</details><br>

#### Create a DaskHub user:

<details>
<summary>Click to expand.</summary>
You can create a user by going to <b><ins>Cognito</ins></b> through the AWS Console, then go to the appropriate <b><ins>User pool</ins></b>, then click on <b><ins>Users</ins></b> from the side-bar on the left, under the <b><ins>User management</ins></b> section, click on <b><ins>Create user</ins></b> and proceed to fill in the information, when it comes to the <b><ins>Invitation message</ins></b> section, make sure you select: <b><ins>Don't send an invitation</ins></b> and instead send your own email.
</details><br>

---

## Common problems:

#### If you are unable to invoke `cdk ls` because of a `ModuleNotFoundError: No module named 'aws_cdk'`:

<details>
<summary>Click to expand.</summary>
This is an ongoing problem/compatibility issue with Windows specifically. If you are not on Windows and are still experiencing this problem, please document your:
<ol>
<li>OS Version</li>
<li>CPU Architecture</li>
<li>platform branch & the commit number you are on</li>
<li>Python version</li>
<li>npm version</li>
<li>Node.js version</li>
<li>CDK version</li>
<li>aws-cli version</li>
</ol>
</details><br>

#### In case DaskHub fails to deploy entirely:

<details>
<summary>1 — Click to expand.</summary>
This may be caused by an unclean environment, delete the <code>.venv</code> directory and the <code>temp</code> directory
<ol>
Remember to remake your <code>venv</code> by running:
<li><code>python -m venv .venv</code></li>
<li><code>source .venv/bin/activate</code></li>
<li><code>pip install -r requirements.txt</code></li>
</ol>
</details><br>

<details>
<summary>2 — Click to expand.</summary>
This may be caused by an unsupported region, make sure the following machine sizes are available in the region:
<ol>
<li>M5n.8xLarge</li>
<li>M4.8xLarge</li>
<li>M5dn.8xLarge</li>
<li>R5dn.8xLarge</li>
</ol>
</details><br>

<details>
<summary>3 — Click to expand.</summary>
This could be caused by now un-used Amazon AWS Registry components in your configuration file, to resolve the issue:
<ol>
<li>Completely tear down your current deployment/attempt</li>
<li>Make sure that Registry databases are also removed/torn down</li>
<li>Comment out or delete the Registry section in your configuration file</li>
<li>Set the Registry component to <code>False</code> in the HelioCloud modules section as such:
<pre>
# Enabling all available HelioCloud modules
enabled:
  registry: False # ← make sure this is False
  portal: True
  daskhub: True
</pre>
</li>
</ol>
</details><br>

#### In case DaskHub deploys but the page does not open when accessed:

<details>
<summary>Click to expand.</summary>
This may be caused by a botched deployment (typically indicative of auto-https failing) which may be because the instance was deployed with unreleased resources.
<ol>
To confirm if <code>auto-https</code> is indeed the culprit:
<li>Log into the admin EC2 machine of your DaskHub instance</li>
<li>run the following command: <code>kubectl get pods -n daskhub</code></li>

</ol>
</details><br>

---

## How can I teardown a DaskHub instance completely?

<details>
<summary>Click to expand.</summary>
<ol>
<li>Log into the admin EC2 machine for your DaskHub instance</li>
<li>run the following commands:
	<ol>
	    <li><code>cd ~</code>
	    <li><code>ls -l</code>
    </ol>
</li>
<li>You will find a shell script named <code>99-delete-daskhub.sh</code>, run this script by typing <code>bash ./99-delete-daskhub.sh</code></li>
<li>After the script has finished running, proceed to <b><ins>CloudFormation</ins></b> to look for and delete the following in-order:
	<ol>
	    <li>instance-name<code>Daskhub</code>A40CC2DB</li>
	    <li>instance-name<code>Portal</code>1D3F8D83</li>
		<li>instance-name<code>RegistrationPage</code>D5002A07</li>
	    <li>instance-name<code>Auth</code>B659ECCE</li>
		<li>instance-name<code>Base</code>DC4C73C4</li>
	</ol>
</li>
<li>Double-check that all the CloudFormation deletions have completed successfully, specifically check for any VPCs that contain your instance-name</li>
</ol>
</details><br>

---
