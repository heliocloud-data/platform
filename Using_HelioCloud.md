# Using HelioCloud - Best Practices
## 4 May 2025

A HelioCloud has two modes of use, the Notebook environment (Daskhub with Jupyter Notebooks), and the Portal for launching cloud machines (Instances).

To get started with the Notebook environment, you log in, select a machine type (standard server, big big server, or GPU server with PyTorch or TensorFlow enabled. You can begin coding or navigate to the "science-tutorials" directory and view 'README.md' for more details (for highest readability, right click, 'Open With -> Markdown Preview').

For Portal Instances, you select the smallest machine (least expensive) for solving your tasks, choose an operating system, launch it, then SSH (remote log in) to it.

## The Daskhub Jupyter Notebook Environment

The Daskhub Notebook environment is fairly safe, cost-wise.  Good cloud stewardship is:
    - choose the appropriate resource rather than always selecting the biggest by default (use the smallest machine size that enables your work)
    - don’t leave stuff on if you aren’t using it
    - try not to store massive amounts of data long-term in your user directories.
 
Just having a basic Notebook session up on the low end machines is negligible, at perhaps \\$2/day, and something you can do without worry. Feasible but more expensive, the ‘Big Big’ server is only \\$5/day. Good stewardship says please do not keep machines up if you aren’t using them.  I believe we use an 8-hour auto-logoff as a guardrail for this.

Accessing data is free.  Using and accessing the NASA TOPS datasets (AIA, CDAWeb, MMS, and contributed datasets), as shown in the tutorials, is free because AWS donated that space to NASA, so the highest potential cost is actually zero for HelioCloud use.
 
Where costs are likely a risk for a project are:
      - Personal disk storage! Storing a lot of data in your HelioCloud home or scratch directories for long periods of time adds up.
      - Instancing a dask cluster of temporary CPUs to do dask ‘bursts’, then not turning them off, accumulates wasted cost over time
 
Both of the above are in the ‘good stewardship’ category versus a ‘do not do’, as the work comes first.  We do track user costs, so if you do something costly, we can open discussions with you.  But the point is for science to get done and the cloud to be available to you without you having to worry, under the ‘Big science from your Browser’ vision.

## Portal Instances

For Portal-generated machines or 'Instances' (called 'EC2' by AWS) the same ‘good stewardship’ rules will exist.  Using the Portal to instance machines you can log into via SSH can potentially incur more costs. Because you can launch powerful machines in Portal, you also can run up your costs very quickly-- some machines cost as high as \\$6 per hour.  Further, Portal machines remain running until you specifically turn them off.  If you, for example, spin up a costly machine then forget to turn it off, that can incur a \\$1000 bill in just a week.

Again, only use the minimum machine necessary for the task.  Remember to Stop any machines you are not currently using.  Also, terminate (delete) any machines no longer needed, otherwise (even turned off) they accumulate disk storage costs.

### Set-up tips for the different Portal EC2 OSes

    - Amazon Linux: Deep Learning has Python 3.12, pip and git installed. AL2023 has python3.9 (as 'python3') and requires 'sudo yum install pip' and 'sudo yum install git' to set up.
    - Ubuntu Linux: Deep Learning has Python 3.12, pip and git installed. Ubuntu 24 has python 3.12 but requires 'sudo yum update' then 'sudo yum install pip' and 'sudo yum install git' to set up.
    - RedHat Linux: RHE1 was python 3.9 (as 'python3') and requires 'sudo yum install pip' and 'sudo yum install git' to set up.