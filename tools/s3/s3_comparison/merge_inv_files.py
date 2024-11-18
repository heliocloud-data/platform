#
# program to take the output of download_s3_inventory files and combine them into one
# master file (which allows better comparison between s3 buckets)
#

import pandas as pd
import argparse

DEF_BATCH_SIZE = 10
DEF_WRITE_HEADER = False
#col_names = ['bucket', 'object', 'version', 'size', 'modtime' ]
col_names = ['bucket', 'object', 'size', 'modtime' ]
#col_names = ['object', 'size']

ap = argparse.ArgumentParser(description='Program to combine inventory csv files.')
ap.add_argument('--output_file', '-o', type=str, help='output file to write merged csv files to', default="merged.csv")
ap.add_argument('--batch_size', '-b', type=int, help='size of batch to use for merging files', default=DEF_BATCH_SIZE)
ap.add_argument('--write_header', '-w', default=False, action='store_true', help='Write a header')
ap.add_argument('files', nargs="+", type=str, help='csv files to use')

args = ap.parse_args()

batch_size =  args.batch_size
if len(args.files) < batch_size:
    batch_size = len(args.files)

batch_cntr = 0
files = args.files
fcntr = 0
while fcntr < len(files):

    cntr = 0
    frames = []
    while cntr < batch_size and fcntr < len(files):

        f = files[fcntr]
        print (f"reading [{fcntr}] {f}")
        df = pd.read_csv(f, header='infer', names=col_names)
        frames.append(df)

        fcntr += 1
        cntr += 1


    if len(frames) > 1:
        merged = pd.concat(frames)
    else:
        merged = frames[0]

    ofilename = f"{batch_cntr}_{args.output_file}" 

    # write sorted key values out to text list
    merged.to_csv(ofilename, columns=['object', 'size'], index=False, header=args.write_header)

    batch_cntr += 1

    print (f"Wrote merged list to {ofilename}")

    del merged 



