"""
Terms:
   TOPS bucket: NASA-provided free S3, s3://gov-nasa-gsfc-data1/
   staging bucket: where to temporarily transfer files into, likely s3://helio-data-staging
   s3destination = eventual final home for the files, likely TOPS bucket
   staging fileRegistry = fileRegistries in the staging bucket
   canonical fileRegistry = fileRegistries in the s3destination

Update process: fetch latest data files, then move to destination and update registries

Fetch latest data files code:
1) get catalog of all CDAWeb IDs
    either local file, fetch of full list, or similar
2) diff against DB:catalog.json to get added or dropped datasets
3) for each ID, get deltas (all items if a new set)
    a) iterate by year
    b) for each item
         if item already exists in canonical fileRegistry, do not fetch or do anything
         otherwise, fetch item, and register to staging fileRegistry
    c) add this id to the 'move-over' list for the next step (unless no changes were done)
    d) optionally, S3 inventory and/or checksum and/or file existence checks on fetched items?
4) for each ID, get GAP file for id
       for each 'old/new' pair, verify new is fetched, and write name of 'old' to 'deleteme' list
5) run 'move-over' code for that ID once ID is entirely done

Move-over code: go from helio-data-staging to TOPS
1) read 'move-over' list indicating which IDs have new/changed contents
2) for each ID:
     a) move files to appropriate s3destination
     b) take new fileRegistry and add to canonical fileRegistry
     c) update db:catalog.json with any change in stopDate, modificationdate, startdate
     d) optionally, S3 Inventory or other check that files were copied over successfully
     e) write destination catalog.json from DB:catalog.json
     f) clean out staging area once safely done
     g) delete and deregister obsolete files from 'deleteme' list

Note that fileRegistries are named [id]_YYYY.csv and consist of a CSV header + lines:
   startdate,s3key,size,any additional items,,,
They reside in the sub-bucket for that [id]
Also, the 'catalog.json' list of holdings is in the root directory of s3destination

Tried using 's3fs' for more elegant writes, but it kept hanging on .close()
so switched to straightforward but less direct boto3 .upload_file()


"""
import s3staging as s3s
import requests
import re
import os
import json
import shutil
import urllib
import boto3
import s3fs
import datetime
from dateutil import parser
from multiprocessing.pool import ThreadPool

""" CDAWeb-specific routines here """

def get_CDAWEB_filelist(dataid,time1,time2):

    ttime1 = s3s.iso2nodash(time1) # weird reformatting for cdaweb url
    ttime2 = s3s.iso2nodash(time2) # weird reformatting for cdaweb url
    
    headers = {"Accept": "application/json"}

    url = 'https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/' + dataid + '/orig_data/' + ttime1 + ',' + ttime2
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        j = res.json()
        # need to provide the local keys for 'key', 'startDate' and 'filesize' plus any extra keys plus the actual 'data'
        #hapiurl = 'https://cdaweb.gsfc.nasa.gov/hapi/info?id='+dataid
        retset={"key": "Name", "startDate": "StartTime", "stopDate": "EndTime", "checksum": None, "checksum_algorithm": None, "filesize": "Length"}
        try:
            retset["data"]=j['FileDescription']
        except:
            s3s.logme("no files for ",dataid+" at "+url,'error')
            retset=None
    else:
        s3s.logme("timeout trying to fetch ",dataid,'error')
        retset=None
    return retset

def get_CDAWEB_IDs(fname,dataid=None,webfetch=True):
    url = 'https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/'
    # first fetch URL, if not read prior stored file
    # curl -s -H "Accept: application/json" https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/ | cat >datasets_all.json

    headers = {"Accept": "application/json"}
    if webfetch:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            try:
                j = res.json()
                if len(j) > 0:
                    s3s.datadump(fname,j,jsonflag=True)
            except:
                s3s.logme("Invalid or incomplete json in request, using earlier copy.",fname,'error')
        else:
            s3s.logme("URL for datasets failed, return code ",res.status_code,'error')
    else:
        s3s.logme("Using local copy of IDs (no web fetch)",fname,'status')

    ids_meta = {}
    j=s3s.dataingest(fname,jsonflag=True)
    if dataid == None:
        ids = [item['Id'] for item in j['DatasetDescription']]
    else:
        ids = [dataid]
    for item in j['DatasetDescription']:
        if dataid == None or dataid == item['Id']:
            ids_meta[item['Id']] = cdaweb_json_to_cloudme_meta(item)
            
    ids.sort()
    
    return ids, ids_meta

def cdaweb_json_to_cloudme_meta(jdata):
    """ sample metadata in each json entry (not all guaranteed to exist):
    Id, Observatory, Instrument, ObservatoryGroup, InstrumentType,
    Label, TimeInterval {Start, End}, PiName, PiAffiliation,
    Notes (a url to notes), SpaseResourceID, DatasetLink {Title, Text, URL}
    
    Mapping to useful CloudMe metadata:
    Label -> title
    PiName -> contact
    SpaseResourceID -> contactID
    Notes -> aboutURL
    all items in DatasetLink concaternated -> description?
    """    
    mymeta = {}
    mymetamap = {"id":"Id","title":"Label","resourceURL":"Notes",
                 "contact":"PiName","contactID":"SpaseResourceID",
                 "aboutURL":"Notes","TimeInterval":"TimeInterval"}

    for k,v in mymetamap.items():
        if v in jdata:
            if k == 'TimeInterval':
                mymeta['startDate'] = jdata[v]['Start']
                mymeta['stopDate'] = jdata[v]['End']
            else:
                mymeta[k]=jdata[v]
    return mymeta
                 
class S3info:
    def __init__(self,s3staging,s3destination,movelogdir,stripuri,extrameta):
        self.s3staging=s3staging
        self.s3destination=s3destination
        self.movelogdir=movelogdir
        self.stripuri=stripuri
        self.extrameta=extrameta
        

def load_cdaweb_params(dataid=None,webfetch=False):
    # CDAWeb-specific data call
    # use webfetch=True to grab and make local cached copy, False to use local cached copy
    localcopy_cdaweblist="datasets_all.json"
    allIDs, allIDs_meta = get_CDAWEB_IDs(localcopy_cdaweblist,dataid=dataid,webfetch=webfetch)

    # Set dataset staging-specific items
    s3staging = "./cdaweb/"  # for now, later s3://helio-data-staging/"
    #s3staging = "s3://antunak1/"
    s3destination = "s3://helio-data-staging/cdaweb/"
    movelogdir = s3staging + "movelogs/"
    stripuri = 'https://cdaweb.gsfc.nasa.gov/sp_phys/data/'
    extrameta = None # optional extra metadata to include in CSV

    sinfo=s3s.bundleme(s3staging,s3destination,movelogdir,stripuri,
                       extrameta)
    
    return sinfo, allIDs, allIDs_meta

def demo(test=True,multicore=False):

    """ can be easily parallelized to 1 dataset per thread.
        To throttle bandwidth further, an extra loop could be added
        per thread to grab 1 year at a time; however, this would
        have to be within the thread not parallel as a single dataid
        uses a single movelog file, and we are not using file locking.
    """
    if test:
        webfetch=False # for speed, use cached copy
    else:
        webfetch=True # for legit, get freshest cdaweb dataIDs list
    sinfo,allIDs,allIDs_meta=load_cdaweb_params(webfetch=webfetch)
    
    if test: s3s.logme("Total CDAWeb IDs: ",len(allIDs),'log')
    allIDs = s3s.remove_processed(sinfo["movelogdir"],allIDs)
    if test: s3s.logme("Unprocessed CDAWeb IDs: ",len(allIDs),'log')

    if test:
        allIDs = [myall for myall in allIDs if myall.startswith("AC_H2")]
        s3s.logme("Test set is ",allIDs,'status')
    
    if multicore:
        with ThreadPool(processes=4) as pool:
            pool.map(fetchCDAWebsinglet,allIDs)
    else:
        for dataid in allIDs:
            fetchCDAWebsinglet(dataid)
        
def fetchCDAWebsinglet(dataid):

    test=1

    if test:
        # using time1, time2 = None, None is only for prod
        time1,time2="2021-12-31T22:00:00Z","2022-01-05T00:00:00Z"
    else:
        # for production runs
        time1,time2=None,None
        
    sinfo,allIDs,allIDs_meta=load_cdaweb_params(dataid=dataid,webfetch=False)

    # Generic setup
    catmeta = s3s.getmeta(dataid,sinfo,allIDs_meta)
    if time1 == None: time1=catmeta['startDate']
    if time2 == None: time2=catmeta['stopDate']
    if test: s3s.logme("Getting",dataid+" "+time1+" - "+time2,'status')

    # CDAWeb-specific fetch (rewrite for each new source/dataset)
    flist = get_CDAWEB_filelist(dataid,time1,time2)
        
    # Generic for any fetch
    if flist != None:
        os.makedirs(sinfo["movelogdir"],exist_ok=True)
        csvreg,sinfo = s3s.fetch_and_register(flist, sinfo)
        # prioritize prescribed keys, if any (debate: is this needed?)
        extrameta = s3s.gatherkeys(sinfo,flist)
        s3s.write_registries(dataid,sinfo,csvreg)
        s3s.ready_migrate(dataid,sinfo,time1,time2,catmeta=catmeta)


demo(test=True,multicore=False)
