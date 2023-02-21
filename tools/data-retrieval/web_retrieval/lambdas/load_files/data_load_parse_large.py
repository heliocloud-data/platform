from io import StringIO
import logging
import glob
import os
import urllib.request
import boto3

# set up the logger to record any error messages - only logging critical errors
log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')


class DataLoaderReader():
    def __init__(self, file_meta):
        self.file_meta = file_meta
        self.source_type = file_meta['source_type']
        self.in_bucket = file_meta['in_bucket']

        # start up the clients
        self.s3 = boto3.client('s3')

        self.run_file_proc()

    @property
    def get_supported_file_types(self):
        return ['cdf']

    def run_file_proc(self):
        if not self.in_bucket:  # query a re-download of the data
            if self.source_type == 'web':
                self.download_file()
            elif self.source_type == 's3':  # s3 transfer
                self.transfer_file()
            else:
                logging.error('Source type not currently supported.')
                raise

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
        urllib.request.urlretrieve(
            url, '/tmp/fileobj.{}'.format(self.file_meta['file_type']))

        # upload the local data to S3
        response = self.s3.upload_file(os.path.join(
            '/tmp/fileobj.{}'.format(self.file_meta['file_type'])), bucket, filename)

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
        self.s3.meta.client.copy(
            copy_source, self.file_meta['s3_bucket'], self.file_meta['s3_filename'])
        # TODO --> delete file from the source bucket


def lambda_handler(event, context):
    file_meta = event['file_meta']

    DataLoaderReader(file_meta)

    return {
        'statusCode': 200,
        'file_meta': file_meta,
        'logging_stream': log_stream.getvalue()
    }
