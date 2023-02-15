import boto3
from datetime import datetime as dt
from dateutil import parser
import logging
import glob
import os
import urllib.request
import cdflib
from io import StringIO

# set up the logger to record any error messages - only logging critical errors
log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')


class DataLoaderReader():
    def __init__(self, file_meta):
        self.file_meta = file_meta
        self.source_type = file_meta['source_type']
        self.in_bucket = file_meta['in_bucket']
        #self.in_register = file_meta['in_register']

        # start up the clients
        self.s3 = boto3.client('s3')
        # self.dynamodb = boto3.resource('dynamodb')

        self.run_file_proc()

    @property
    def get_supported_file_types(self):
        return ['cdf']

    # TODO remove database items, VLT commented out
    def run_file_proc(self):
        if self.in_bucket == False:  # query a re-download of the data
            if self.source_type == 'web':
                    self.download_file()
                    #self.read_register_file(file_loaded=True)
            elif self.source_type == 's3':  # s3 transfer
                    self.transfer_file()
                    #self.read_register_file(file_loaded=False)
            else:
                logging.error('Source type not currently supported.')
                raise

        # elif self.in_register == False:
        #     self.read_register_file(file_loaded=False)

    def download_file(self):
        '''
        Will download the file from the internet
        :param file_meta:
        :return:
        '''
        filename = self.file_meta['s3_filename']
        url = self.file_meta['download_url']
        bucket = self.file_meta['s3_bucket']

        # determine if the tmp directory is already full and if so delete anything in it
        if glob.glob('/tmp/*'):
            for i in glob.glob('/tmp/*'):
                os.remove(i)

        # save url contents to a local file
        urllib.request.urlretrieve(url, '/tmp/fileobj.{}'.format(self.file_meta['file_type']))

        # upload the local data to S3
        response = self.s3.upload_file(os.path.join('/tmp/fileobj.{}'.format(self.file_meta['file_type'])), bucket, filename)

    def transfer_file(self):
        '''
        Will transfer the file from another s3 bucket to the staging bucket
        :param file_meta:
        :return:
        '''
        # grab the bucket name and key of the source and then copy to the new bucket
        # assumes a file structure in the url of 's3://<bucket>/<key>
        source_info = self.file_meta['download_url'].split('//')[-1].split('/')
        source_bucket = source_info[0]
        source_key = source_info[1]
        # we are just changing the bucket - preserve the key structure
        copy_source = {
            'Bucket': source_bucket,
            'Key': source_key
        }
        self.s3.meta.client.copy(copy_source, self.file_meta['s3_bucket'], self.file_meta['s3_filename'])
        # TO DO --> delete file from the source bucket

    def read_register_file(self, file_loaded=True):
        '''
        Reads in the file based on the file type, using appropriate libraries
        Registers in the base file register dynamodb
        Updates the summary dynamodb
        The file has only been preloaded to the Lambda /tmp directory if we are grabbing it from the internet
        :param file_meta:
        :return:
        '''
        if file_loaded == False: # pull the file into the tmp directory
            # determine if the tmp directory is already full and if so delete anything in it
            if glob.glob('/tmp/*'):
                for i in glob.glob('/tmp/*'):
                    os.remove(i)

            s3_bucket = self.file_meta['s3_bucket']
            s3_filename = self.file_meta['s3_filename']
            self.s3.download_file(s3_bucket, s3_filename, '/tmp/fileobj.{}'.format(self.file_meta['file_type']))

        if self.file_meta['file_type'] in self.get_supported_file_types:
            if self.file_meta['file_type'] == 'cdf':
                # read in the csv type
                self.file_obj = cdfReader(self.file_meta)

            # TO DO ADD OTHER FILE READERS
            self.register_item()
            self.update_summary_table()
        else:
            # print error that the file type is not currently supported
            logging.error('File type is not currently supported. Supported file types = {}'.format(self.get_supported_file_types))
            raise

    def register_item(self):
        '''
        Establish a connection with the DynamoDB Table and register the object
        :param db_item:
        :return:
        '''
        filereg_table = self.dynamodb.Table('fileRegister')
        filereg_table.put_item(Item=self.file_obj.db_item)

    def update_summary_table(self):
        '''
        Update the summary table to account for the new object being registered
        '''
        summary_table = self.dynamodb.Table('dataSummary')
        # query table for this data product
        response = summary_table.get_item(
            Key={
                'mission': self.file_obj.db_item['mission'],
                'dataset': self.file_obj.db_item['dataset']
            }
        )
        if 'Item' in response:
            item = response['Item']
            # determine if any relevant parameters have been changed in the file
            date_range_change = False
            variable_change = False

            # first compare the date range
            if (item['dataset_start'] > self.file_obj.db_item['start_date']) | \
                    (item['dataset_end'] < self.file_obj.db_item['end_date']):
                date_range_change = True

            # second compare the variables
            in_table_vars = set(item['variables'])

            if self.file_obj.vars.difference(in_table_vars):
                variable_change = True

            # if either one changed then we update the item
            if date_range_change | variable_change:
                if response['Item']['dataset_start'] > self.file_obj.db_item['start_date']:
                    item['dataset_start'] = self.file_obj.db_item['start_date']
                elif response['Item']['dataset_end'] < self.file_obj.db_item['end_date']:
                    item['dataset_end'] = self.file_obj.db_item['end_date']

                if variable_change:
                    in_table_vars = in_table_vars.union(self.file_obj.vars)
                    item['variables'] = in_table_vars

                # change the modification date for the item - this will alert any subscribers to the data product
                item['dataset_update'] = dt.now().isoformat()

                # put the new item back in to the table
                summary_table.put_item(Item=item)

        else:
            # item is not in the table so register the data
            db_item_summary = {
                'mission': self.file_obj.db_item['mission'],
                'dataset': self.file_obj.db_item['dataset'],
                'dataset_start': self.file_obj.db_item['start_date'],
                'dataset_end': self.file_obj.db_item['end_date'],
                'instrument': self.file_obj.db_item['instrument'],
                'variables': self.file_obj.vars,
                'dataset_update': self.file_obj.db_item['dataset_update']
            }
            summary_table.put_item(Item=db_item_summary)


class cdfReader():
    '''
    Class wrapping the reading of a CDF file
    '''
    def __init__(self, file_meta):
        self.file_meta = file_meta
        self.load_obj_reader()

    def load_obj_reader(self):
        '''
        Loads the CDF file using cdflib, pulls out the relevant information,
        Dumps to dynamoDB for registry
        :param s3_bucket:
        :param s3_filename:
        :return:
        '''
        # will raise an error if the validation fails - other errors could also happen
        self.cdfobj = cdflib.CDF('/tmp/fileobj.cdf', validate=True)
        self.get_cdf_attributes()


    def get_cdf_attributes(self):
        '''
        Pulls out the CDF attributes for storage in the dynamoDB
        :param cdf_file:
        :return:
        '''
        cdf_info = self.cdfobj.cdf_info()

        # grab the version number if present
        try:
            version = cdf_info['Version']
        except:
            version = ''
            logging.warning('No version number present in the file')

        # grab all of the variables
        zvars = cdf_info['zVariables']

        # grab the start and stop time of the file
        # this will spit out a time string which divees down into microseconds
        epoch_time = self.cdfobj.varget('Epoch')
        start_time = cdflib.cdfepoch.encode(epoch_time[0])
        end_time = cdflib.cdfepoch.encode(epoch_time[-1])
        start_time_epoch = cdflib.cdfepoch.unixtime(epoch_time[0])[0]
        end_time_epoch = cdflib.cdfepoch.unixtime(epoch_time[-1])[0]

        # get the current date
        upload_date = dt.now().isoformat()

        print('Start time = {}'.format(start_time))
        print('End time = {}'.format(end_time))

        # edit the mission to be a concatenation of mission and spacecraft if a spacecraft field is present
        if self.file_meta['sc']:
            mission = '_'.join([self.file_meta['mission'], self.file_meta['sc']])
        else:
            mission = self.file_meta['mission']

        # create a dictionary of all the relevant attributes to be used for upload
        self.db_item = {
            's3_filekey': self.file_meta['s3_filename'],
            'dataset': self.file_meta['dataset'],
            'start_date': start_time,
            'end_date': end_time,
            'mission': mission,
            'instrument': self.file_meta['instr'],
            'level_processing': self.file_meta['level_proc'],
            'dataset_update': upload_date,
            'source_update': self.file_meta['source_update'],
            'version': version,
        }

        self.vars = set(zvars)



def lambda_handler(event, context):
    file_meta = event['file_meta']

    DataLoaderReader(file_meta)

    return {
        'statusCode': 200,
        'file_meta': file_meta,
        'logging_stream': log_stream.getvalue()
    }