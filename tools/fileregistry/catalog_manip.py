import json
from filelock import FileLock, Timeout

catalogName = "catalog.json"


def lock_close(lock):
    lock.release()


def lock_open():
    lockfile = catalogName + ".lock"
    status = False

    lock = FileLock(lockfile, timeout=4)
    try:
        lock.acquire()
        status = True
    except Timeout:
        print("File locked by other program, failing")
    except:
        print("Unknown file lock error")

    return status, lock


def ingest_catalog(catalogName, lock=False):
    with open(catalogName, "r") as f:
        catData = json.load(f)

    return catData


def display_catalog(catData):
    for item in catData["catalog"]:
        print("\n", item["id"])
        for mykey in item.keys():
            print("    ", mykey, ":", item[mykey])


def query_form():
    keys = [
        "id",
        "loc",
        "title",
        "startdate",
        "enddate",
        "modificationdate",
        "indexformat",
        "fileformat",
    ]
    ownerkeys = ["description", "resourceID", "creationDate", "citation", "contact", "aboutURL"]

    dataset = {}
    for mykey in keys:
        data = input(mykey + ": ")
        dataset[mykey] = data

    return dataset


def add_entry(catData, dataset):
    catData["catalog"].append(dataset)


def write_catalog(catalogName, catData):
    status, lock = lock_open()

    if status:
        with open(catalogName, "w") as f:
            json.dump(catData, f, indent=4)

        lock_close(lock)

    return status


def check_unique(catData, dataset):
    idset = [dataset["id"] for dataset in catData["catalog"]]
    if dataset["id"] in idset:
        return False
    else:
        return True


catData = ingest_catalog(catalogName)
display_catalog(catData)

newEntry = query_form()  # {"id":"test","loc":"s3://whatever","title":"Hi"}
print(check_unique(catData, newEntry))

if check_unique(catData, newEntry):
    add_entry(catData, newEntry)
    display_catalog(catData)
    status = write_catalog(catalogName, catData)
    print("New file written: ", status)

print(check_unique(catData, newEntry))
