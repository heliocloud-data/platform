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

""" General driver routines here, should work for most cases """

def bundleme(s3staging,s3destination,movelogdir,stripuri,extrameta):
    # core items needed for any run
    sinfo={"s3staging":s3staging,
           "s3destination":s3destination,
           "movelogdir":movelogdir,
           "stripuri":stripuri,
           "extrameta":extrameta
           }
    return sinfo

def logme(message,data="",type='status'):
    if type == 'error':
        print("Error:",message,data)
    elif type == 'log':
        print("Log:",message,data)
    else: # just an onscreen status
        print("Status:",message,data)

def get_lastModified(item):
    # fetch last modified date for that ID
    # for now, just hard-coded
    lasttime="20230101T000000Z"
    return lasttime

def getHAPIIDs(lasttime, catalogurl):
    # no longer needed, we fetch from CDAWeb itself now
    # catalogurl = "https://cdaweb.gsfc.nasa.gov/hapi/catalog"
    res = requests.get(catalogurl)
    j = res.json()
    if res.status_code == 200:
        return [item["id"] for item in j['catalog'] if get_lastModified(item) > lasttime]
    else:
        return None
    
    
def make_subdirs_orig(mybase,fname):
    # used to use make_subdirs(s3staging,s3stub), obsoleted with better path calls
    #fpath = '/'.join((fname.split('/'))[:-1])
    steps = re.sub('/$','',mybase) # rare case of not needing ending /
    localpath = (fname.split('/'))[:-1]
    for subdir in localpath:
        steps += '/' + subdir
        if not os.path.isdir(steps):
            os.mkdir(steps)
            logme("Making ",steps)
            
def s3url_to_bucketkey(s3url):
    # S3 paths are weird, bucket + everything else, e.g.
    # s3://b1/b2/b3/t.txt would be bucket b1, file b2/b3/t.txt
    name2 = re.sub(r's3://','',s3url)
    s=name2.split('/')
    mybucket=s[0]
    myfilekey = '/'.join(s[1:])
    return mybucket, myfilekey
        

def fetch_and_register(filelist, sinfo):
    """ requires input filelist contain the following items:
    "data" array containing file description dictionary that includes
        the URI to fetch and minimum metadata of 'startDate', 'filesize',
        optional defined keys 'stopDate','checksum','checksum_algorithm',
        and optional undefined 'extrameta' keywords
    "key" field indicating the data dictionary field name for URI
    "startDate" field indicating the data dict field name for startDate
    "filesize" field indicating the data dict field name for filesize,
    optional additional metadata or None if none exist

    stripuri = fetching URL to replace with s3staging
    """
    lastpath = "/" # used later to avoid os calls

    csvregistry = []

    startkey = filelist['startDate']
    filesizekey = filelist['filesize']

    if sinfo["s3staging"].startswith("s3://"):
        mys3 = boto3.client('s3')

    for item in filelist["data"]:
        url_to_fetch = item[filelist['key']]
        logme("fetching ",url_to_fetch)
        s3stub = re.sub(sinfo["stripuri"],'',url_to_fetch)
        stagingkey = sinfo["s3staging"] + s3stub
        s3key = sinfo["s3destination"] + s3stub
        # make any necessary subdirectories in staging
        (head,tail) = os.path.split(stagingkey)
        try:
            registryloc = os.path.commonprefix([registryloc, head])
        except:
            registryloc = head
        if head != lastpath:
            os.makedirs(head,exist_ok=True)
            lastpath = head
        if stagingkey.startswith("s3://"):
            mybucket, myfilekey = s3url_to_bucketkey(stagingkey)
            tempfile = '/tmp/'+re.sub(r'/|:','_',stagingkey)
            urllib.request.urlretrieve(url_to_fetch,tempfile)
            mys3.upload_file(tempfile,mybucket,myfilekey)
            os.remove(tempfile)
        else:
            urllib.request.urlretrieve(url_to_fetch,stagingkey)
            
        csvitem = item[startkey] + ',' + s3key + ',' + str(item[filesizekey])
        if filelist['stopDate'] != None:
            csvitem += ',' + item[filelist['stopDate']]
        if filelist['checksum'] != None:
            csvitem += ',' + item[filelist['checksum']]
        if filelist['checksum_algorithm'] != None:
            csvitem += ',' + item[filelist['checksum_algorithm']]
        if sinfo["extrameta"] != None:
            for extrakey in sinfo["extrameta"]:
                csvitem += ',' + item[extrakey]
    
        logme(csvitem)
        csvregistry.append(csvitem)

    # clean registryloc to remove any year stub
    registryloc = re.sub(r'\d{4}$','',registryloc)
    if not re.search(r'/$',registryloc):
        registryloc += '/' # all locs end in a '/'
    logme('final destination was: ',registryloc,'log')

    return registryloc,csvregistry

def registryname(id,year):
    if year.isdigit():
        regname = id + '_' + str(year) + '.csv'
    else:
        regname = id + '_' + year + '.csv'
    return regname

def local_vs_s3_open_notused(fname,mode):
    # currently not working for s3fs reads (crashes) or writes (hangs)
    if fname.startswith("s3://"):
        s3 = s3fs.S3FileSystem(anon=True)
        fopen = s3.open(fname,mode+'b')
    else:
        fopen = open(fname,mode)
    return fopen

def exists_anywhere(fname):
    if fname.startswith("s3://"):
        s3_client = boto3.client('s3')
        mybucket, myfilekey = s3url_to_bucketkey(fname)
        try:
            s3_client.get_object(Bucket=mybucket,Key=myfilekey)
            return True
        except s3_client.exceptions.NoSuchKey:
            return False
    else:
        if os.path.exists(fname):
            return True
        else:
            return False


def dataingest(fname,jsonflag=False):
    if fname.startswith("s3://"):
        s3 = boto3.resource('s3')
        mybucket, myfilekey = s3url_to_bucketkey(fname)
        s3object = s3.Object(mybucket,myfilekey)
        #tempdata = s3object.get()['Body'].read().decode('utf-8')
        tempdata = s3object.get()['Body'].read().decode()
        if jsonflag:
            tempdata=json.loads(tempdata)
    else:
        with open(fname,'r') as fin:
            if jsonflag:
                tempdata=json.load(fin)
            else:
                tempdata = fin.read()
            
    return tempdata


def datadump(fname,tempdata,jsonflag=False):
    # works for local or S3
    # later, debate adding open(fname,'w',encoding='utf-8')
    if fname.startswith("s3://"):
        mys3 = boto3.client('s3')

        mybucket, myfilekey = s3url_to_bucketkey(fname)
        tempfile = '/tmp/'+re.sub(r'/|:','_',fname)
        with open(tempfile,'w') as fout:
            if jsonflag:
                json.dump(tempdata,fout,indent=4,ensure_ascii=False)
            else:
                fout.write(tempdata)
        mys3.upload_file(tempfile,mybucket,myfilekey)
        os.remove(tempfile)
    else:
        with open(fname,'w') as fout:
            if jsonflag:
                json.dump(tempdata,fout,indent=4,ensure_ascii=False)
            else:
                fout.write(tempdata) # local write

def uniquejson(jobj,masterkey,uniquekey):

    movie = jobj[masterkey]
    unique_stuff = {elem[uniquekey]:elem for elem in movie}.values()
    
    jobj[masterkey]=[]
    for ele in unique_stuff:
        jobj[masterkey].append(ele)
    return jobj


def replaceIsotime(catData,mykey,maybetime):
    # non-optimized way to conditionally replace an isotime in the catalog
    # if isotime does not exist, it gets added as an element
    unfound = True
    for i in range(len(catData['catalog'])):
        for key in catData['catalog'][i]:
            if key == mykey:
                unfound = False
                if maybetime > catData['catalog'][i][key]:
                    catData['catalog'][i][key]=maybetime

    if unfound:
        catData['catalog'].append({mykey:maybetime})
                    
    return catData

def cda2iso(timey):
    # converts most any isotime to our specific string format
    # annoying reformat of YYYYMMDDTHHMMSSZ to YYYY:MM:DDTHH:MM:SSZ
    r=parser.parse(timey)
    timey=r.strftime("%Y-%m-%dT%H:%M:%SZ")
    #timey=datetime.datetime.fromisoformat(timey).isoformat() # only for python>3.11
    #timey = timey[0:4]+':'+timey[4:6]+':'+timey[6:11]+':'+timey[11:13]+':'+timey[13:]
    return timey

def iso2nodash(timey):
    # removes dashes to what cdaweb curl expects
    # so time1="2022-01-01T00:00:00Z" -> time1="20220101T000000Z"
    r=parser.parse(timey)
    timey=r.strftime("%Y%m%dT%H%M%SZ")
    return timey


def write_registries(id,registryloc,csvregistry,extrameta=None):
    """ creates files <id>_YYYY.csv with designated entries
    in the temporary directory s3staging+id/ which will later be moved
    (by the separate staging-to-production code)
    to the location as defined in catalog.csv as the field 'loc'
    """
    keyset=['startDate','key','filesize']
    if extrameta != None: keyset += extrameta

    currentyear="1000" # junk year to compare against

    os.makedirs(registryloc,exist_ok=True)

    for line in csvregistry:
        year=line[0:4]
        if year != currentyear:
            try:
                datadump(fname,tempdata)
            except:
                pass
            currentyear = year
            fname = registryloc+registryname(id,currentyear)
            logme("Creating registry ",fname,'log')
            header = '#' + ','.join(keyset) + "\n"
            tempdata = header
        line += "\n"
        tempdata += line
    datadump(fname,tempdata)


def create_catalog_stub(dataid,registryloc,s3staging,
                        catmeta,startDate,stopDate,appendflag=False):

    """ Generates a catalog_stub.json file, suitable for
    adding to the s3destination catalog.json after merging.
    Location is s3staging+dataid+'/'+catalog_stub.json

    We use read-add-write rather than append because S3 lacks append-ability

    Note if you append it will add the same id and info to the catalog stub
    everytime you run the code.  The default is append=False because typical
    use is to create 1 stub in the destination that matches that one dataset.
    But I kept the append flag in case it is needed for future cases.

    typical optional catmeta are from the spec, e.g.:
    "catalog": [
            "id": "euvml",
            "loc": "gov-nasa-helio-public/euvml/",
            "title": "EUV-ML dataset",
            "startDate": "1995-01-01T00:00Z",
            "stopDate": "2022-01-01T00:00Z",
            "modificationDate": "2022-01-01T00:00Z",
	    "indexformat": "csv",
	    "fileformat": "fits",
	    "description": "Optional description for dataset",
	    "resourceURL": "optional identifier e.g. SPASE ID",
	    "creationDate": "optional ISO 8601 date/time of the dataset creation",
	    "citation": "optional how to cite this dataset, DOI or similar",
	    "contact": "optional contact info, SPASE ID, email, or ORCID",
	    "aboutURL": "optional website URL for info, team, etc"    
    """

    catalogkeys = ['id','loc','title',
                   'startDate','stopDate','modificationDate',
                   'indexformat','fileformat','description','resourceURL',
                   'creationDate','citation','contact','aboutURL']
    
    fstub = registryloc + 'catalog_stub.json'
    if appendflag and exists_anywhere(fstub):
        catData = dataingest(fstub,jsonflag=True)
    else:
        # new catalog
        catData = {"catalog":[]}

    for mykey in catalogkeys:
        if mykey in catmeta:
            catData['catalog'].append({mykey:catmeta[mykey]})

    catData = replaceIsotime(catData,'startDate',startDate)
    catData = replaceIsotime(catData,'stopDate',stopDate)

    datadump(fstub,catData,jsonflag=True)
    logme("Wrote catalog stub ",fstub,'log')
    
def blank_catalog(dataid):
    catalogkeys = ['id','loc','title',
                   'startDate','stopDate','modificationDate',
                   'indexformat','fileformat','description','resourceURL',
                   'creationDate','citation','contact','aboutURL']
    catalog={}
    catalog['id']=dataid
    return catalog
    
def hapi_info_to_catdata(dataid,hapiurl):
    """
    For datasets that have a HAPI info endpoint, fetch metadata from it
    Other datasets will need their own parsers for getting metadata
    """
    
    catalogkeys = ['id','loc','title',
                   'startDate','stopDate','modificationDate',
                   'indexformat','fileformat','description','resourceURL',
                   'creationDate','citation','contact','aboutURL']

    headers = {"Accept": "application/json"}
    res = requests.get(hapiurl, headers=headers)
    if res.status_code == 200:
        try:
            j = res.json()
            print('hapi j',j)
        except:
            print("failed with url ",hapiurl)
            j=blank_catalog(dataid)

    catmeta = {}
    for mykey in catalogkeys:
        if mykey in j['parameters']:
            catmeta[mykey]=j[mykey]
        
    return catmeta

def gatherkeys(sinfo,flist):
    # THIS IS TERRIBLE CODE
    optkeys = []
    if flist["stopDate"] != None: optkeys.append('stopDate')
    if flist["checksum"] != None: optkeys.append('checksum')
    if flist["checksum_algorithm"] != None: optkeys.append('checksum_algorithm')
    if sinfo["extrameta"] != None:
        sinfo["extrameta"] = optkeys + sinfo["extrameta"]
    elif len(optkeys) > 0:
        extrameta = optkeys
    return extrameta
                
def remove_processed(movelogdir,allIDs):
    """ go through movelog to figure out which IDs are already completed
    then remove them
    """
    for dataid in allIDs:
        movelog = movelogdir + 'movelog_' + dataid + '.json'
        if exists_anywhere(movelog):
            allIDs.remove(dataid)

    return allIDs


def getmeta(dataid,allIDs_meta):
    if dataid in allIDs_meta:
        catmeta = allIDs_meta[dataid]
    else:
        # try HAPI
        try:
            hapiurl = 'https://cdaweb.gsfc.nasa.gov/hapi/info?id='+dataid
            catmeta = s3s.hapi_info_to_catdata(dataid,hapiurl)
        except:
            catmeta = s3s.blank_catalog(dataid)
    return catmeta


def ready_migrate(dataid,sinfo,registryloc,startDate,stopDate,
                  catmeta={}):
    """
    once an item is properly staged, this lists it in a file
    so the subsequent migration to the s3 destination knows what to
    process.
    Format of each entry is:
    dataid, s3destination, s3staging, s3subdir, registrloc, catalog_stub
    where
    s3destination is where the files will ultimately reside
    s3staging+s3subdir is where they currently are
    registryloc is location of staging <id>_YYYY.csv files
    catalog_stub is the part to amalgamate into the final catalog.json

    migration is simply
    'cp -r <s3staging>/<s3subdir> <s3destination>/<s3subdir>'
    then update <s3destination>/catalog.json with <catalog_stub>
    
    """

    create_catalog_stub(dataid,registryloc,sinfo["s3staging"],
                        catmeta,startDate,stopDate)

    # elegant way to get the first subdir where the actual data exists
    s3subdir = registryloc.split(sinfo["s3staging"])[1].split('/')[0] + '/'

    entry = {"dataid": dataid,
             "s3destination": sinfo["s3destination"],
             "s3staging": sinfo["s3staging"],
             "s3subdir": s3subdir,
             "registryloc": registryloc,
             "catalog_stub": registryloc+'catalog_stub.json'}

    movelog = sinfo["movelogdir"] + 'movelog_' + dataid + '.json'

    if exists_anywhere(movelog):
        logme("Updating movelog ",movelog+" with "+dataid,'log')
        movelist = dataingest(movelog,jsonflag=True)
    else:
        logme("Creating movelog ",movelog+" with "+dataid,'log')
        movelist={'movelist':[]}

    movelist['movelist'].append(entry)
    movelist=uniquejson(movelist,'movelist','dataid')
    datadump(movelog,movelist,jsonflag=True)
            


        
def migrate_staging_to_s3():
    """
    The later actual migration will involve
     a) move files to appropriate s3destination
     b) take new fileRegistry and add to canonical fileRegistry
     c) update db:catalog.json with any change in stopDate, modificationdate, startdate
     d) optionally, S3 Inventory or other check that files were copied over successfully
     e) write destination catalog.json from DB:catalog.json
     f) clean out staging area once safely done
     g) delete and deregister obsolete files from 'deleteme' list
    """
    pass

