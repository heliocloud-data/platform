"""
A more generic version of 'make_file_database.py' which is specific to the MMS data
author = klyeakel
date = 6/24/2022
"""

import os
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import numpy as np
import re
import boto3
import datetime


class ProductDatabase:
    def __init__(self, data_request, destination_bucket):
        """
        Defines the instrument, mode, level and product desired
        :param instrument:
        :param mode:
        :param level:
        :param product:
        """
        self.product = data_request["product"]
        self.mission = data_request["mission"]
        self.sc = data_request["sc"]
        self.instr = data_request["instr"]
        self.levelproc = data_request["levelproc"]
        self.instr_mode = data_request["instr_mode"]
        self.source_type = data_request["source_type"]
        self.source = data_request["source"]  # document where the data is coming from
        self.dest_bucket = destination_bucket

        self.clean_product_name()
        print("Scraping file data for {}".format(self.product_name))

        # first look at the page which lists the years of data
        self.fetch_main_cdaweb_req()
        # for each year, find the months where we have data - this will create a dictionary of year - month list
        self.fetch_month_req()
        # look through each month and grab the individual file path and their descriptors
        self.fetch_filepaths()

    def clean_product_name(self):
        """
        Cleans up the product name so it appears nicely in the DynamoDB
        :return:
        """
        product_name = [self.mission, self.sc, self.instr, self.instr_mode, self.levelproc]
        product_name = [i for i in product_name if i]  # removes any attributes that are None
        self.product_name = "_".join(product_name)

    def request_html(self, path):
        # grab the html content
        response = requests.get(path, verify=False)  #'/Users/root_certificate.pem')
        if response.status_code != 200:
            print("Error! Could not fetch the page :(")
            content = None
        else:
            content = response.content
        return content

    def href_year(self, href_string):
        """
        returns true if the href is a year
        :return:
        """
        applicable_years = [
            "{}/".format(i) for i in np.arange(2015, 2023)
        ]  #   EDIT THIS IF YOU WANT MORE DATA
        if href_string in applicable_years:
            return True
        else:
            return False

    def href_month(self, href_string):
        """
        returns true if the href is a month
        :param href_string:
        :return:
        """
        applicable_months = [
            "01/",
            "02/",
            "03/",
            "04/",
            "05/",
            "06/",
            "07/",
            "08/",
            "09/",
            "10/",
            "11/",
            "12/",
        ]
        if href_string in applicable_months:
            return True
        else:
            return False

    def fetch_main_cdaweb_req(self):
        """
        Fetchs the master CDAWEB website reference point
        :param sc:
        :param instrument:
        :param mode:
        :param level:
        :param product:
        :return:
        """
        self.core_path = "https://cdaweb.gsfc.nasa.gov/pub/data/{}".format(self.product)

        content = self.request_html(self.core_path)
        if content is None:
            exit()
        else:
            soup = bs(content, "html.parser")

            # first pull out the years - find the hrefs that are years
            year_links = soup.find_all(href=self.href_year)
            self.years = [i.contents[0].replace("/", "") for i in year_links]

    def fetch_month_req(self):
        """
        For each year, make request and find the months coinciding
        :return:
        """
        self.year_months = dict()

        for y in self.years:
            # build the request
            req = "{}{}".format(self.core_path, y)
            content = self.request_html(req)
            if content:
                soup = bs(content, "html.parser")
                month_links = soup.find_all(href=self.href_month)
                months = [i.contents[0].replace("/", "") for i in month_links]
                self.year_months[y] = months

    def calc_file_size(self, size_string):
        """
        Output will be float representing file size in MB
        :param size_string:
        :return:
        """
        size_string = size_string.strip()
        if "K" in size_string:
            size_float = float(size_string.split("K")[0])
            size_float = size_float / 1000.0
        elif "M" in size_string:
            size_float = float(size_string.split("M")[0])
        elif "G" in size_string:
            size_int = float(size_string.split("G")[0])
            size_float = size_int * 1000.0
        elif "T" in size_string:
            size_int = float(size_string.split("T")[0])
            size_float = size_int * 1000000.0
        else:
            size_float = 0
        return size_float

    def fetch_filepaths(self):
        """
        Cycles through the year-month dictionary and pulls out the individual filepaths and their associated descriptors
        Builds a dataframe of files present on CDAWEB that are being staged for upload
        :return:

        Create dataframe with files and associated meta data for easy indexing on the cloud
        1: Index, integer (this is arbitrary)
        2: S3 key, this is filepath excluding bucket
        3: S3 bucket
        4: CDAWEB source filepath
        5: Date file last modified on CDAWEB
        6: CDAWEB filesize estimate, float, in MB
        7: Mission
        8: Spacecraft (can be Nan, only valid for multi s/c mission)
        9: Instrument
        10: Mode
        11: Level
        12: Product (can be Nan - not all instruments have multiple products, e.g. FGM)
        13: Year
        14: Month
        15: Sample Date - grabbed from filename on CDAWEB
        16: Date uploaded to S3 and validated - NaN if not on S3
        17: Is Valid flag, boolean/Nan, indicates whether CDF was validated on S3 using MD5 checksum, NaN if validation was not run
        """
        total_download_size = 0

        self.master_dataframe = pd.DataFrame()
        for year, month_list in self.year_months.items():
            # build the html request
            for month in month_list:
                req = "{}/{}/{}/".format(self.core_path, year, month)
                content = self.request_html(req)
                if content:
                    soup = bs(content, "html.parser")
                    # find all the links corresponding to a CDF file
                    cdf_links = soup.findAll(href=re.compile("\.cdf"))

                    # find the parent for each cdf link and get the last modified dates and rough file size
                    parents = [i.parent.parent for i in cdf_links]
                    filepaths = [i.contents[0].contents[0].contents[0] for i in parents]
                    filepaths = [i.strip() for i in filepaths]

                    modified_date = [i.contents[1].contents[0] for i in parents]
                    modified_date = [i.strip() for i in modified_date]

                    size_string = [i.contents[2].contents[0] for i in parents]
                    size_string = [i.strip() for i in size_string]
                    size_float = [self.calc_file_size(i) for i in size_string]
                    size_chunk = np.sum(size_float)
                    total_download_size = total_download_size + size_chunk

                    # build up the dataframe entries
                    index = np.arange(len(filepaths))

                    s3_root = self.core_path.split("/")[5:]
                    # s3_root[0] = s3_root[0].upper() # do not put the mission in uppercase
                    s3_root = "/".join(s3_root)
                    s3_keys_df = ["{}{}/{}/{}".format(s3_root, year, month, i) for i in filepaths]

                    cdaweb_sourcefile_df = [
                        "{}{}/{}/{}".format(self.core_path, year, month, i) for i in filepaths
                    ]

                    s3_bucket_df = np.tile(self.dest_bucket, len(filepaths))
                    product_df = np.tile(self.product_name, len(filepaths))
                    mission_df = np.tile(self.mission, len(filepaths))
                    sc_df = np.tile(self.sc, len(filepaths))
                    instr_df = np.tile(self.instr, len(filepaths))
                    levelproc_df = np.tile(self.levelproc, len(filepaths))
                    instr_mode_df = np.tile(self.instr_mode, len(filepaths))
                    source_type_df = np.tile(self.source_type, len(filepaths))
                    source_df = np.tile(self.source, len(filepaths))
                    year_df = np.tile(int(year), len(filepaths))
                    month_df = np.tile(int(month), len(filepaths))

                    sample_date_df = [i.split("_")[-2] for i in filepaths]

                    # data_uploaded_df = np.tile(np.nan, len(filepaths))
                    #
                    # data_valid_df = np.tile(np.nan, len(filepaths))

                    calc_file_size = np.tile(
                        np.nan, len(filepaths)
                    )  # this is Nan until calculated officially on file verification

                    tmp_df = pd.DataFrame(
                        {
                            "s3_key": s3_keys_df,
                            "s3_bucket": s3_bucket_df,
                            "source_path": cdaweb_sourcefile_df,
                            "mission": mission_df,
                            "sc": sc_df,
                            "product": product_df,
                            "instr": instr_df,
                            "instr_mode": instr_mode_df,
                            "level_proc": levelproc_df,
                            "source": source_df,
                            "source_type": source_type_df,
                            "year": year_df,
                            "month": month_df,
                            "sample_date": sample_date_df,
                            "estimated_file_size_mb": size_float,
                            "calc_file_size_mb": calc_file_size,
                            "source_update": modified_date,
                        }
                    )
                    self.master_dataframe = self.master_dataframe.append(tmp_df, ignore_index=True)

        # fix the date columns
        self.master_dataframe["sample_date"] = pd.to_datetime(self.master_dataframe["sample_date"])
        print("Total download size estimated at {} GB".format(total_download_size / 1000.0))


def build_multi_request(list_reqs, outdir, request_tag, destination_bucket):
    """
    Creates the multi-prong request from list of requests from user
    :param list_reqs:
    :return:
    """
    master_db = pd.DataFrame()

    for req in list_reqs:
        db = ProductDatabase(req, destination_bucket)
        master_db = master_db.append(db.master_dataframe, ignore_index=True)

    # truncate the database solely for testing reasons
    # master_db = master_db.iloc[:100]
    master_db.to_pickle(os.path.join(outdir, "{}.pkl".format(request_tag)))
    master_db.to_csv(os.path.join(outdir, "{}.csv".format(request_tag)))
    return master_db


def upload_to_s3(db, bucket_name, request_tag):
    """
    Read the credentials in the aws credentials file -- do not keep this info in the script
    :param db:
    :param bucketname:
    :return:
    """
    # upload the request to s3
    session = boto3.Session(profile_name="006885615091_CT-PowerUser-HelioCloud")
    s3 = session.client("s3", use_ssl=True, verify="/Users/yeakekl2/root_certificate.pem")

    # break down the original csv file into 5k chunks of files - prevents overwhelming state machine event history
    num_request_items = len(db)
    num_chunks = int(np.ceil(num_request_items / 2000))
    chunks = np.array_split(db, num_chunks)
    for i, c in enumerate(chunks):
        tmp_filename = os.path.join(outdir, "{}_masterchunk{}.csv".format(request_tag, i))
        c.to_csv(tmp_filename)
        with open(tmp_filename, "rb") as f:
            s3.upload_fileobj(f, bucket_name, "upload_manifest/{}.csv".format(request_tag))


def make_request_dict(
    product, mission, spacecraft, instr, levelproc, instr_mode, source, source_type
):
    """
    Builds up a dictionary based on all the desired data
    :param product:
    :param mission:
    :param instr:
    :param levelproc:
    :param instr_mode:
    :param source:
    :return:
    """
    request = {
        "product": product,
        "mission": mission,
        "sc": spacecraft,
        "instr": instr,
        "levelproc": levelproc,
        "instr_mode": instr_mode,
        "source": source,  # document where the data is coming from
        "source_type": source_type,
    }
    return request


if __name__ == "__main__":
    outdir = os.path.join(os.getcwd(), "upload_request")
    request_tag = "mag_test_brst_" + "upload_manifest"
    MISSION = "MMS"
    # SC = ['MMS1', 'MMS2', 'MMS3', 'MMS4']
    SC = ["MMS1"]

    destination_bucket = "test-cdaweb"

    req_list = []
    # generate a list of requests
    for s in SC:
        req_list.append(
            make_request_dict(
                "mms/mms1/fgm/srvy/l2/", "mms", "mms1", "fgm", "l2", "srvy", "SPDF", "web"
            )
        )
        #
        # req_list.append(Request(MISSION, s, 'feeps', 'srvy', 'l2', 'electron'))
        # req_list.append(Request(MISSION, s, 'feeps', 'srvy', 'l2', 'ion'))
        # req_list.append(Request(MISSION, s, 'feeps', 'brst', 'l2', 'electron'))
        # req_list.append(Request(MISSION, s, 'feeps', 'brst', 'l2', 'ion'))
        #
        # req_list.append(Request(MISSION, s, 'fpi', 'brst', 'l2', 'des-dist'))
        # req_list.append(Request(MISSION, s, 'fpi', 'brst', 'l2', 'dis-dist'))
        # req_list.append(Request(MISSION, s, 'fpi', 'fast', 'l2', 'des-moms'))
        # req_list.append(Request(MISSION, s, 'fpi', 'fast', 'l2', 'dis-moms'))
        #
        # req_list.append(Request(MISSION, s, 'epd-eis', 'brst', 'l2', 'electronenergy'))
        # req_list.append(Request(MISSION, s, 'epd-eis', 'brst', 'l2', 'extof'))

        # req_list.append(Request(MISSION, s, 'edp', 'brst', 'l2', 'dce', 1))
        # req_list.append(Request(MISSION, s, 'edp', 'brst', 'l2', 'scpot', 2))
        # req_list.append(Request(MISSION, s, 'fgm', 'brst', 'l2', None, 3))

    # pass the request lister to the builder and make the request dataframe
    db = build_multi_request(req_list, outdir, request_tag, destination_bucket)

    # upload to s3
    # upload_to_s3(db, 'data-upload-queue', request_tag)
    upload_to_s3(db, "data-upload-trigger", request_tag)
