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
     c) update db:catalog.json with any change in enddate, modificationdate, startdate
     d) optionally, S3 Inventory or other check that files were copied over successfully
     e) write destination catalog.json from DB:catalog.json
     f) clean out staging area once safely done
     g) delete and deregister obsolete files from 'deleteme' list

Note that fileRegistries are named [id]_YYYY.csv and consist of a CSV header + lines:
   startdate,s3key,size,any additional items,,,
They reside in the sub-bucket for that [id]
Also, the 'catalog.json' list of holdings is in the root directory of s3destination

"""



import requests
import re
import os
import json
import shutil
import urllib
import boto3
import s3fs

""" General driver routines here, should work for most cases """

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
            print("Making ",steps)
        

def fetch_and_register(filelist, stripuri, s3destination, s3staging,
                       extrameta=None):
    """ requires input filelist contain the following items:
    "data" array containing file description dictionary that includes
        the URI to fetch and minimum metadata of 'startDate', 'filesize',
        optional defined keys 'endDate', 'checksum' and 'checksum_algorithm',
        and optional undefined 'extrameta' keywords
    "key" field indicating the data dictionary field name for URI
    "startDate" field indicating the data dict field name for startDate
    "filesize" field indicating the data dict field name for filesize,
    optional additional metadata or None if none exist
    """
    lastpath = "/" # used later to avoid os calls

    csvregistry = []

    startkey = filelist['startDate']
    filesizekey = filelist['filesize']
    
    for item in filelist["data"]:
        url_to_fetch = item[filelist['key']]
        print("fetching ",url_to_fetch)
        s3stub = re.sub('https://cdaweb.gsfc.nasa.gov/sp_phys/data/','',url_to_fetch)
        stagingkey = s3staging + s3stub
        s3key = s3destination + s3stub
        # make any necessary subdirectories in staging
        (head,tail) = os.path.split(stagingkey)
        if head != lastpath:
            os.makedirs(head,exist_ok=True)
            lastpath = head
        urllib.request.urlretrieve(url_to_fetch,stagingkey)
        
        csvitem = item[startkey] + ',' + s3key + ',' + str(item[filesizekey])
        if filelist['endDate'] != None:
            csvitem += ',' + item[filelist['endDate']]
        if filelist['checksum'] != None:
            csvitem += ',' + item[filelist['checksum']]
        if filelist['checksum_algorithm'] != None:
            csvitem += ',' + item[filelist['checksum_algorithm']]
        if extrameta != None:
            for extrakey in extrameta:
                csvitem += ',' + item[extrakey]
    
        print(csvitem)
        csvregistry.append(csvitem)

    return csvregistry

def registryname(id,year):
    if year.isdigit():
        regname = id + '_' + str(year) + '.csv'
    else:
        regname = id + '_' + year + '.csv'
    return regname

def local_vs_s3_open(fname,mode):
    if fname.startswith("s3://"):
        s3 = s3fs.S3FileSystem(anon=True)
        fopen = s3.open(fname,mode+'b')
    else:
        fopen = open(fname,mode)
    return fopen

def write_annual_registry(id,s3staging,csvregistry,extrameta=None):
    """ creates files <id>_YYYY.csv with designated entries
    in the temporary directory s3staging+id/ which will later be moved
    (by the separate staging-to-production code)
    to the location as defined in catalog.csv as the field 'loc'
    """
    keyset=['startDate','key','filesize']
    if extrameta != None: keyset += extrameta

    currentyear="1000" # junk year to compare against
    
    for line in csvregistry:
        year=line[0:4]
        if year != currentyear:
            try:
                fout.close()
            except:
                pass
            currentyear = year
            registryloc = s3staging+id
            os.makedirs(registryloc,exist_ok=True)
            fname = s3staging+id+'/'+registryname(id,currentyear)
            print("Creating registry ",fname)
            fout = local_vs_s3_open(fname,"w")
            header = '#' + ','.join(keyset)
            fout.write(header+"\n")
        fout.write(line+"\n")
    fout.close()


def create_catalog_stub(dataid,s3staging):
    """ Generates a catalog_stub.json file, suitable for
    adding to the s3destination catalog.json after merging.
    Location is s3staging+dataid+'/'+catalog_stub.json

    We use read-add-write rather than append because S3 lacks append-ability
    """
    fstub = s3staging+dataid+'/catalog_stub.json'
    if os.path.exists(fstub):
        fin=local_vs_s3_open(fstub,"r")
        catData = json.load(fin)
        fin.close()
    else:
        # new catalog
        catData = {"catalog":[]}

    entry = {"tbd": "tbd"}






    
    catData['catalog'].append(entry)
    









    fout=local_vs_s3_open(fstub,"w")
    json.dump(catData,fout,indent=4,ensure_ascii=False)
    fout.close()

    

""" CDAWeb-specific routines here """


def get_cdaweb_filelist(dataid,time1,time2):

    headers = {"Accept": "application/json"}

    url = 'https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/' + dataid + '/orig_data/' + time1 + ',' + time2
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        j = res.json()
        # need to provide the local keys for 'key', 'startDate' and 'filesize' plus any extra keys plus the actual 'data'
        return {"key": "Name", "startDate": "StartTime", "endDate": "EndTime", "checksum": None, "checksum_algorithm": None, "filesize": "Length", "data": j['FileDescription']}
    else:
        print("Timeout trying to fetch ",dataid)
        return None



def get_cdaweb_IDs(fname,webfetch=True):
    url = 'https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/'
    # first fetch URL, if not read prior stored file
    # curl -s -H "Accept: application/json" https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/ | cat >datasets_all.json

    # tbd: update with local_vs_s3_open(fname,mode) (no 'a' in S3?)
    
    headers = {"Accept": "application/json"}
    if webfetch:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            try:
                j = res.json()
                if len(j) > 0:
                    with open(fname,'w',encoding='utf-8') as fout:
                        json.dump(j,fout,indent=4,ensure_ascii=False)
            except:
                print("Invalid or incomplete json in request, using earlier copy.")
        else:
            print("URL for datasets failed, return code ",res.status_code)
    else:
        print("Using local copy of IDs (no web fetch)")
        
    with open(fname,'r') as fin:
        j=json.load(fin)
        ids = [item['Id'] for item in j['DatasetDescription']]
        ids.sort()
    return ids

def demo():
    #dataid = 'AC_H0_MFI'
    s3destination = "s3://helio-data-staging/cdaweb/"
    s3staging = "./"  # for now, later s3://helio-data-staging/"
    datasets_fname="datasets_all.json" # local copy of periodically-fetched CDAWeb canonical list of ids
    time1="20220101T000000Z"
    time2="20220505T000000Z"
    stripuri = 'https://cdaweb.gsfc.nasa.gov/sp_phys/data/'

    # option list of extra metadata that the CSV will contain
    extrameta = None
    
    allIDs = get_cdaweb_IDs(datasets_fname,False)
    print("There are ",len(allIDs)," CDAWeb IDs")
    for dataid in allIDs:
        if dataid == "PSP_COHO1HR_MERGED_MAG_PLASMA":  # HACK FOR TESTING!!!
            flist = get_cdaweb_filelist(dataid,time1,time2)
            csvregistry = fetch_and_register(flist, stripuri, s3destination, s3staging,extrameta=extrameta)
            # prescribed keys, if any

            # THIS IS TERRIBLE CODE
            optkeys = []
            if flist['endDate'] != None: optkeys.append('endDate')
            if flist['checksum'] != None: optkeys.append('checksum')
            if flist['checksum_algorithm'] != None: optkeys.append('checksum_algorithm')
            if extrameta != None:
                extrameta = optkeys + extrameta
            elif len(optkeys) > 0:
                extrameta = optkeys

                
            registryloc=write_annual_registry(dataid,s3staging,csvregistry,extrameta=extrameta)
            ready_to_migrate(dataid,s3staging,registryloc)



            

            
def ready_to_migrate(dataid,s3staging,registryloc,movelog='move-over.json'):
    """
    once an item is properly staged, this lists it in a file
    so the subsequent migration to the s3 destination knows what to
    process.
    Format of each entry is:
    dataid, current s3staging base, location of staging <id>_YYYY.csv files

    Actual migration involves
     a) move files to appropriate s3destination
     b) take new fileRegistry and add to canonical fileRegistry
     c) update db:catalog.json with any change in enddate, modificationdate, startdate
     d) optionally, S3 Inventory or other check that files were copied over successfully
     e) write destination catalog.json from DB:catalog.json
     f) clean out staging area once safely done
     g) delete and deregister obsolete files from 'deleteme' list
    """

    create_catalog_stub(dataid,s3staging)

    entry = {"dataid": dataid,
             "s3staging": s3staging,
             "registryloc": registryloc}

    if os.path.exists(movelog):
        print("Updating movelog with ",dataid)
        fin = local_vs_s3_open(movelog,'r')
        movelist=json.load(fin)
        fin.close()
    else:
        print("Creating movelog with ",dataid)
        movelist={'movelist':[]}

    movelist['movelist'].append(entry)
    
    fout=local_vs_s3_open(movelog,"w")
    json.dump(movelist,fout,indent=4,ensure_ascii=False)
    fout.close()
        
        
def migrate_staging_to_s3():
    pass


demo()
