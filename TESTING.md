# HelioCloud Daskhub/Portal/Runtimes Test Plan

Once a HelioCloud is built, this testing must be passed in order to achieve a public release.  This plan describes testing which must be passed in order to achieve a public release. Must be tested at two different institutions and by at least 2 different people at each: one installing it, the other acting as the test user.

## Admin/Signup Page Test (est. time > 10 minutes)

1. Add 2 new users directly
2. Have 2 new users request accounts
   - reject 1 of the 2, verify the rejected account not created

## Portal Tests (est. time < 20 minutes)

A user will log into Portal and verify these operations succeed:

1. Test Portal keygen
   - make a Keypair
   - make an LT Access Key
   - generate a Token

2. Generating an EC2 of each OS choice
   - Generate EC2
   - Log into it
   - Run and logging into it to run sample Python code (which tests general python functionality, S3 access and ability to read CDFs)
```
import cdflib
import math
s3name="s3://gov-nasa-hdrl-data1/demo-data/mms_fgm.cdf"
cdfin1 = cdflib.CDF(s3name)
assert math.isclose(sum(sum(cdfin1['mms1_fgm_b_gse_brst_l2'])), 415662.265625)
cdfin1.close()
```

This test code produces no output, but errors out if any part fails.

3. Look at Costing information, ensure it it displayed

## Region Testing (all server types) (est. time up up to 1 hour)

1. Login as Admin User
     - Spin up every type of server-- check the number of activate instances when back to 0 in the console to verify it's a cold start. 
     
     **Note:** Before running a cold start test, you'll want to make sure that there are no available instances in the cluster.  The easiest way to do that is to scale down all the EKS node groups to `0`; using the `eksctl` command.

     From the EKS Admin machine, type the following:
      ```
      eksctl scale nodegroup --cluster=<cluster-name> --name=<node-group> --nodes=0 --region=<region>
      ```

     The result should look something like this:     
      ```
      sh-4.2$ eksctl scale nodegroup --cluster=eks-helio --name=mng-user-compute --nodes=0 --region=us-east-2
      2025-01-29 22:15:13 [ℹ]  scaling nodegroup "mng-user-compute" in cluster eks-helio
      2025-01-29 22:15:15 [ℹ]  initiated scaling of nodegroup
      2025-01-29 22:15:15 [ℹ]  to see the status of the scaling run `eksctl get
      ```
      
     This operation can take several minutes to be fufilled.  To confirm the number of instances, type the following command.
      ```
      kubectl get nodes -o json | jq '.items[].metadata|select(.labels."eks.amazonaws.com/nodegroup"=="<node-group>")'
      ```

     Nothing should be printed.
     - Document time to spin up each server (cold starts). Verify no timeouts.  Record time it takes (no firm criteria needed here)
     (To guarantee a cold start, for that target instance, check that to fit your server it must make a new EC2 instance. Easiest way is 'nothing has been run before it')
     - Shut down that server.
     
2. Login as Regular User
     - Spin up every type of server.  
     - Time to spin up each server should be ≤ 5 minutes (warm starts) (<30 seconds is preferable but 5 min is  a hard fail). Verify no timeouts.  
     - run the 'Testing_Notebook.ipynb' Notebook
     - Shut down that server.

## Daskhub CPU Detailed Tests - Run only in smallest CPU server (est. time < 1 hour)

1. PRIMARY TEST
   - Running all top-level Tutorials from the 'README.md' and log any errors. If any fail, discuss whether this holds up v1.1 or not– often is easier to update the Tutorial than fix the Runtime.

2. Git Plugin Test
   - In 'science tutorials' do a Git Pull, verify it works.

3. EFS Mount Test (file tab functionality)
   - Upload a file into the home directory
   - Create a folder in the home directory
   - Download a file from the home directory
   - Upload a file into the scratch/ space
   - Create a folder in the scratch/ space
   - Download a file from the scratch/ space

4. Terminal Access
   - Create a terminal and verify it starts (warning, APL usage often requires shifting to 'Classic' mode first)

5. Long-running Kernel Test
   - Test kernel/session stability for 8 hours using:  
     ```python
     from datetime import datetime as dt
     import time
     for i in range(500):
         print(i, dt.now())
         time.sleep(60)
     ```

## Daskhub GPU/ML Tests

   - We don't have a specific test for this yet.

## Uninstall
   - Run Uninstall script
   - Verify all components are destroyed in AWS region except:  
      - EFS.  
      - KMS.  
      - S3.  
      - Persistent volume in EBS (under EC2).
