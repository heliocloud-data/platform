# HelioCloud Change Log
# 10 Feb 2026

## v1-2 (Barbet, Beagle, Bloodhound, Boxer, Bulldog) - 2025-02-1?
	
### Added
	- New 'create an S3 bucket' in Portal for users
	- Default S3 volume mounted for site (internal to site only)
	- Daskhub shows machine costs on Server Options page
	- (2) Jupyter GPU Tutorials
	- Daskhub additions: jupyterlab-plotly, jupyter-ai, juptyer-archive extensions
	- Bleeding Edge:
	    - Daskhub has jupyter-ai
	    - /scratch_space visible to daskhub workers if in same zone
	    - s3fs-fuse in as a hook for future improvements on S3 access

### Changed
	- Improved Portal page, shows more instances, shows S3 - costs, better VM costing
	- Improved login (OAuth) and logos now addable.
	- Container updates (many) including SunPy & PySPEDAS updates, emacs-nox, lftp
	- Costing improved, including:
 	    - better updates and summaries
	    - summary costs on Portal page
	    - S3 costs shown on Portal page
	- Under the hood:
	    - Cluster ingress reconfigure improved portal/daskhub login
	    - Daskhub reverse proxy reduces load balancer costs ($768/yr)
	    - Updated AMI choices
	    - Additional Daskhub burst instances added for more reliable start-up    
    	    - Deprecated RHEL, focusing on AWSLinux & Ubuntu
    	    - Updated kubernetes to 1.33 (good through July 29 2027)
    	    - Registration page moved into the cluster
    	    - Auto-makes scratch user directories
	- Daskhub ipydatagrid, bqplot removed

### Fixed
	- lots of bug fixes, install fixes, teardown fixes
	
	
## 4 May 2025
## v1-1 (Akita) - 2025-03-04

### Added
        - Additional Daskhub and Portal capabilities
        - Cost panel for admin tracking of per-user spending via KubeCost
          (see website or daskhub/COST_MONITORING.md)
        - An updated container with strong PyHC	Python support
        - Ability to burst GPUs as well as CPUs
        - Both TensorFlow and PyTorch GPU-based images available
        - User interface and minor feature improvements

### Changed
	- JupyterLab 4.2
	- Python 3.11
	- CloudCatalog v1.0.2
	- PyHC cores and versions: HAPI, Kamodo, PlasmaPy, pySat, pySpedas, SpacePy, SunPy; also AstroPy, AIAPy, other PyHC packages
	- Kubernetes v3.2

### Fixed
        - Better stability for Daskhub
        - More costing information for Portal EC2 instances
        - Ability to git-pull new Tutorials as they're released
        - Improvements in the installation and deployment scripts
        - Numerous minor tweaks and fixes

	
