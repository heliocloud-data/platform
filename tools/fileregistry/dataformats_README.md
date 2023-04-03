# Data Formats

Exploring and testing data formats in the cloud
(Test data formats for both storage and HAPI-like streaming and make recommendations)

Effort 1 -- Exploring and testing data formats in the cloud

The highest urgency item is to understand the implications of putting existing data holdings into cloud storage systems.  Most Heliophysics datasets containing measurements from NASA missions are in CDF (CDF Data Format, 2021) or FITS (Wells, 1981) format, with some data also in netCDF (netCDF Data Format, 2021) or HDF (HDF Data Format, 2021) formats.    We will study the implications of moving CDF and FITS files to the cloud. Question to be addressed in our study include: 
- can unchanged CDF files be efficiently accessed from AWS storage options?
- should CDF data be migrated to a cloud-native format such as zarr? (zarr Data Format, 2021)
- what impact would conversion to zarr have on data volumes?
- if we do need to change formats from CDF to zarr, what infrastructure changes will this drive?
- how are existing streaming services such as the Heliophysics Application Programmer’s Interface (HAPI) (HAPI Data Specification, 2021) affected by file format choices (keeping CDF and FITS, or switching to zarr)?
promote this new fundamental data file standard for the Heliophysics cloud-computing community and report on future opportunities of development to strengthen this standard.

