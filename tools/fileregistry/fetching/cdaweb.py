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
         if item already exists in canonical fileRegistry,
               do not fetch or do anything
         otherwise, fetch item, and register to staging fileRegistry
    c) add this id to the 'move-over' list for the next step
       (unless no changes were done)
    d) optionally, S3 inventory and/or checksum and/or
       file existence checks on fetched items?
4) for each ID, get GAP file for id
       for each 'old/new' pair, verify new is fetched,
       and write name of 'old' to 'deleteme' list
5) run 'move-over' code for that ID once ID is entirely done

Move-over code: go from helio-data-staging to TOPS
1) read 'move-over' list indicating which IDs have new/changed contents
2) for each ID:
     a) move files to appropriate s3destination
     b) take new fileRegistry and add to canonical fileRegistry
     c) update db:catalog.json with any change in
        stopDate, modificationdate, startdate
     d) optionally, S3 Inventory or other check that
        files were copied over successfully
     e) write destination catalog.json from DB:catalog.json
     f) clean out staging area once safely done
     g) delete and deregister obsolete files from 'deleteme' list

Note that fileRegistries are named [id]_YYYY.csv and
consist of a CSV header + lines:
   startdate,s3key,size,any additional items,,,
They reside in the sub-bucket for that [id]
Also, the 'catalog.json' list of holdings is in
the root directory of s3destination

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

# import s3fs
import datetime
from dateutil import parser
from multiprocessing.pool import ThreadPool

""" CDAWeb-specific routines here """


def get_CDAWEB_filelist(dataid, time1, time2):
    ttime1 = s3s.iso2nodash(time1)  # weird reformatting for cdaweb url
    ttime2 = s3s.iso2nodash(time2)  # weird reformatting for cdaweb url

    headers = {"Accept": "application/json"}

    url = "https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/"
    url += dataid + "/orig_data/" + ttime1 + "," + ttime2
    try:
        res = requests.get(url, headers=headers)
        stat = res.status_code
    except:
        stat = -1
    if stat == 200:
        j = res.json()
        # need to provide the local keys for 'key', 'startDate' and 'filesize'
        # plus any extra keys plus the actual 'data'
        # hapiurl = "https://cdaweb.gsfc.nasa.gov/hapi/info?id="+dataid
        retset = {
            "key": "Name",
            "startDate": "StartTime",
            "stopDate": "EndTime",
            "checksum": None,
            "checksum_algorithm": None,
            "filesize": "Length",
        }
        try:
            retset["data"] = j["FileDescription"]
        except:
            s3s.logme(dataid + " no files at", url, "error")
            retset = None
    else:
        s3s.logme("timeout trying to fetch ", dataid, "error")
        retset = None
    return retset


def get_CDAWEB_IDs(fname, dataid=None, webfetch=True):
    url = "https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/"
    # first fetch URL, if not read prior stored file
    # curl -s -H "Accept: application/json" https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/ | cat >datasets_all.json

    if not webfetch and not os.path.exists(fname):
        webfetch = True

    headers = {"Accept": "application/json"}
    if webfetch:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            try:
                j = res.json()
                if len(j) > 0:
                    s3s.datadump(fname, j, jsonflag=True)
            except:
                s3s.logme(
                    "Invalid or incomplete json in request, using earlier copy.", fname, "error"
                )
        else:
            s3s.logme("URL for datasets failed, return code ", res.status_code, "error")
    else:
        s3s.logme("Using local copy of IDs (no web fetch)", fname, "log")

    ids_meta = {}
    j = s3s.dataingest(fname, jsonflag=True)
    if dataid == None:
        ids = [item["Id"] for item in j["DatasetDescription"]]
    else:
        ids = [dataid]
    for item in j["DatasetDescription"]:
        if dataid == None or dataid == item["Id"]:
            ids_meta[item["Id"]] = cdaweb_json_to_cloudme_meta(item)

    ids.sort()

    return ids, ids_meta


def cdaweb_json_to_cloudme_meta(jdata):
    """sample metadata in each json entry (not all guaranteed to exist):
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
    mymetamap = {
        "id": "Id",
        "title": "Label",
        "resourceURL": "Notes",
        "contact": "PiName",
        "contactID": "SpaseResourceID",
        "aboutURL": "Notes",
        "TimeInterval": "TimeInterval",
    }

    for k, v in mymetamap.items():
        if v in jdata:
            if k == "TimeInterval":
                mymeta["startDate"] = jdata[v]["Start"]
                mymeta["stopDate"] = jdata[v]["End"]
            else:
                mymeta[k] = jdata[v]
    return mymeta


class S3info:
    def __init__(self, s3staging, s3destination, movelogdir, stripuri, extrameta):
        self.s3staging = s3staging
        self.s3destination = s3destination
        self.movelogdir = movelogdir
        self.stripuri = stripuri
        self.extrameta = extrameta


def test_fetchCDAWebsinglet(dataid):
    time1, time2 = "2021-12-31T22:00:00Z", "2022-01-05T00:00:00Z"
    fetchCDAWebsinglet(dataid, time1=time1, time2=time2)


def fetchCDAWebsinglet(dataid, time1=None, time2=None):
    sinfo, allIDs, allIDs_meta = load_cdaweb_params(dataid=dataid, webfetch=False)

    # Generic setup
    catmeta = s3s.getmeta(dataid, sinfo, allIDs_meta)
    if time1 == None:
        time1 = catmeta["startDate"]
    if time2 == None:
        time2 = catmeta["stopDate"]
    s3s.logme(dataid + " Getting timerange", time1 + " - " + time2 + " at", "status")

    # CDAWeb-specific fetch (rewrite for each new source/dataset)
    flist = get_CDAWEB_filelist(dataid, time1, time2)

    # Generic for any fetch
    if flist != None:
        if not sinfo["movelogdir"].startswith("s3://"):
            os.makedirs(sinfo["movelogdir"], exist_ok=True)
        csvreg, sinfo = s3s.fetch_and_register(flist, sinfo, logstring=dataid)

        if csvreg is not None:
            # prioritize prescribed keys, if any (debate: is this needed?)
            extrameta = s3s.gatherkeys(sinfo, flist)
            s3s.write_registries(dataid, sinfo, csvreg)
            s3s.ready_migrate(dataid, sinfo, time1, time2, catmeta=catmeta)


def cdaweb_prod(
    threads=1, logfile=None, loglevel=None, refreshIDs=False, limit=None, test=True, stripMMS=False
):
    """
    threads
    logfile
    loglevel
    refreshIDs
    limit = fetch no more than 'limit' IDs, default None = get all cdaweb
    test = pulls only a subset of IDs over a truncated time range
    """

    """ can be easily parallelized to 1 dataset per thread.
        To throttle bandwidth further, an extra loop could be added
        per thread to grab 1 year at a time; however, this would
        have to be within the thread not parallel as a single dataid
        uses a single movelog file, and we are not using file locking.
    """
    if refreshIDs:
        webfetch = True  # for legit, get freshest cdaweb dataIDs list
    else:
        webfetch = False  # for speed, use cached copy

    # loglevel = [None/info, debug, error]
    s3s.init_logger(logfile=logfile, loglevel=loglevel)
    logstr1 = f"logfile {logfile}, loglevel {loglevel}, threads {threads},"
    logstr2 = f"limit {limit}, refreshIDs {refreshIDs}, test {test}, stripMMS {stripMMS}"
    s3s.logme(logstr1, logstr2, "log")

    sinfo, allIDs, allIDs_meta = load_cdaweb_params(webfetch=webfetch)

    if stripMMS:
        s3s.logme("Stripping MMS", "", "log")
        allIDs = [myall for myall in allIDs if not myall.startswith("MMS")]
    else:
        s3s.logme("Fetching full CDAWeb set", "", "log")

    if test:
        allIDs = [myall for myall in allIDs if myall.startswith("AC_H2")]
        s3s.logme("Test set is ", allIDs, "log")

    tally1 = len(allIDs)
    allIDs = s3s.remove_processed(sinfo["movelogdir"], allIDs)
    tally2 = len(allIDs)
    s3s.logme(f"CDAWeb IDS: total {tally1}, unprocessed {tally2}", "", "log")

    if limit:
        allIDs = allIDs[:limit]

    if threads > 1:
        with ThreadPool(processes=threads) as pool:
            if test:
                pool.map(test_fetchCDAWebsinglet, allIDs)
            else:
                pool.map(fetchCDAWebsinglet, allIDs)
    else:
        for dataid in allIDs:
            if test:
                test_fetchCDAWebsinglet(dataid)
            else:
                fetchCDAWebsinglet(dataid)

    s3s.mastermovelog(sinfo["movelogdir"], allIDs)


def load_cdaweb_params(dataid=None, webfetch=False):
    """CDAWeb-specific data call
    use webfetch=True to grab and make local cached copy,
        webfetch=False to use local cached copy
    """
    # Set dataset staging-specific items
    s3destination = "s3://gov-nasa-hdrl-data1/cdaweb/"

    s3staging = "s3://helio-data-staging/cdaweb/"

    """ 'local' means copy TO a local disk rather than S3
        'fetchlocal' means fetch FROM a local disk instead of a URI
    """
    local = False  # False # test case toggle
    if local:
        s3staging = "./cdaweb/"

    # fetchlocal = '/Users/antunak1/gits/heliocloud/tools/fileregistry/fetching/storage2/'
    fetchlocal = None  # 'None' for default URI fetch, disk loc otherwise

    localcopy_cdaweblist = "datasets_all.json"
    allIDs, allIDs_meta = get_CDAWEB_IDs(localcopy_cdaweblist, dataid=dataid, webfetch=webfetch)

    # more configs
    movelogdir = s3staging + "movelogs/"
    stripuri = "https://cdaweb.gsfc.nasa.gov/sp_phys/data/"
    extrameta = None  # optional extra metadata to include in CSV

    sinfo = s3s.bundleme(s3staging, s3destination, movelogdir, stripuri, extrameta, fetchlocal)

    return sinfo, allIDs, allIDs_meta


"""
Note a bug with using 'limit' is CDAWeb fetches that error out
stil count towards that limit, so if you have a limit=8 and 8 dataIDs
error out, every time you re-run you will still be calling those same
errored ones.
"""

PRODUCTION = False

if PRODUCTION:
    # lname="cdaweb_log.txt", or None to log to screen
    lname = "cdaweb_log.txt"
    # stat='error' to only log errors, 'info' as most useful, or 'debug' as verbose
    loglevel = "info"  # info
    # test=True is quick test on a subset, False=everything for production
    test = False  # False #True
    # refreshIDs=False is use local copy, True=possibly iffy webfetch
    refreshIDs = False
    # tcount is tunable, 1 = single thread, >1 = multiprocessing
    tcount = 8
    # limit=N, fetch only N IDs, default None aka get all cdaweb
    limit = None  # None # 20
    # retries, repeat fetch to try unfetched/errored items again, in case network was temporarily down
    retries = 3
    # also edit 'local' and 'fetchlocal' in load_cdaweb_params()
else:
    # test mode
    lname = "cdaweb_log.txt"
    loglevel = "info"
    test = True
    refreshIDs = False
    tcount = 1
    limit = 20
    retries = 3
    # also edit 'local' and 'fetchlocal' in load_cdaweb_params()

    # new schema is to loop it in batches so it updates the logs and caches
# even when several runs time out

gather = False  # if runs foobarred and left partials, this does a cleanup
if gather:
    sinfo, allIDs, allIDs_meta = load_cdaweb_params(webfetch=False)
    s3s.mastermovelog(sinfo["movelogdir"], allIDs)


for i in range(retries):
    cdaweb_prod(
        threads=tcount,
        logfile=lname,
        loglevel=loglevel,
        refreshIDs=refreshIDs,
        limit=limit,
        test=test,
        stripMMS=True,
    )
"""
    except:
        # cleanup code here.  It's slow (has to read S3 for all
        # potential log files) but faster than re-fetching datasets
        s3s.logme("Failed with run",i,"error")
        sinfo,allIDs,allIDs_meta=load_cdaweb_params(webfetch=False)
        s3s.mastermovelog(sinfo["movelogdir"],allIDs)
"""

"""
Notes for testing vs production

Testing:
   1) set 'PRODUCTION = False' at line 312
   2) If copying to a local directory, set 'local = True' at line 284
      otherwise if copying to S3, keep 'local = False' at line 284
   3) If fetching from the web like usual, set 'fetchlocal = None' at line 288
      otherwise, if fetching from a locally mounted disk on storage 2, edit
      'fetchlocal' at line 288 to point to the storage2 drives

Production:
   1) set 'PRODUCTION = True' at line 312
      optionally, edit 'tcount' at line 324 for the # of threads to run simo
   2) Set 'local = False' at line 284 so it writes to S3
   3) If fetching from the web like usual, set 'fetchlocal = None' at line 288
      otherwise, if fetching from a locally mounted disk on storage 2, edit
      'fetchlocal' at line 288 to point to the storage2 drives
"""
