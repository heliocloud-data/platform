import boto3
import os
import hashlib
import io


class S3CDF:
    def __init__(self, s3_object):
        self.s3_object = s3_object
        print(self.s3_object)
        self.position = 0

    def __repr__(self):
        return "<{} s3_object = {}>".format(type(self).__name__, self.s3_object)

    @property
    def size(self):
        return self.s3_object["ContentLength"]

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.position = offset
        elif whence == io.SEEK_CUR:
            self.position += offset
        elif whence == io.SEEK_END:
            if offset >= 0:
                raise ValueError("Offset must be negative if seeking from end of file")
            else:
                # self.position = self.content_length + offset
                self.position = self.size + offset
        else:
            raise ValueError(
                "Invalid whence {}, should be {}, {}, or {}".format(
                    whence, io.SEEK_SET, io.SEEK_CUR, io.SEEK_END
                )
            )

        return self.position

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def read(self, num_bytes=-1):
        if num_bytes == -1:
            stream = self.s3_object["Body"].read()
        else:
            stream = self.s3_object["Body"].read(num_bytes)
            self.seek(offset=num_bytes, whence=io.SEEK_CUR)

        return stream

    def readable(self):
        return True


def validate_file(bucket, key):
    """
    Function to stream the bucket contents using the s3 client and validate with the internal MD5 key
    Replicates the functionality from CDF lib
    """
    obj = s3.get_object(Bucket=bucket, Key=key)  # returns a streaming object

    f = S3CDF(obj)
    md5 = hashlib.md5()
    block_size = 16384
    f.seek(-16, 2)
    print(f.size)
    remaining = f.tell()
    print(remaining)

    while remaining > block_size:
        data = f.read(block_size)
        remaining = remaining - block_size
        md5.update(data)

    if remaining > 0:
        data = f.read(remaining)
        md5.update(data)

    existing_md5 = f.read(16).hex()

    return md5.hexdigest() == existing_md5


if __name__ == "__main__":
    bucket_name = "helio-public"
    main_dataset = "MMS"
    sc = "mms1"
    instrument = "feeps"
    mode = "srvy"
    level = "l2"
    parameter = "electron"
    year = "2017"
    month = "01"
    name = "mms1_feeps_srvy_l2_electron_20170102000000_v6.1.3.cdf"
    s3_object = os.path.join(
        main_dataset, sc, instrument, mode, level, parameter, year, month, name
    )

    s3 = boto3.client("s3")

    is_valid = validate_file(bucket_name, s3_object)
    print(is_valid)
    # obj = s3.get_object(Bucket=bucket_name, Key = s3_object)
    # s3_cdf = S3CDF(obj)
