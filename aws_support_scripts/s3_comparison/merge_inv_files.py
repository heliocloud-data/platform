#
# program to take the output of download_s3_inventory files and combine them into one
# master file (which allows better comparison between s3 buckets)
#

import pandas as pd
import argparse

#col_names = ['bucket', 'object', 'version', 'size', 'modtime' ]
col_names = ['bucket', 'object', 'size', 'modtime' ]

ap = argparse.ArgumentParser(description='Program to combine inventory csv files.')
ap.add_argument('--output_file', '-o', type=str, help='output file to write merged csv files to', default="merged.csv")
ap.add_argument('files', nargs="+", type=str, help='csv files to use')

args = ap.parse_args()


frames = []
for f in args.files:
   df = pd.read_csv(f, header=None, names=col_names)
   frames.append(df)

if len(frames) > 1:
    merged = pd.concat(frames)
else:
    merged = frames[0]

# write sorted key values out to text list
merged.to_csv(args.output_file, columns=['object', 'size'], index=False, header=False)

#print (f"Wrote merged list to {args.output_file}")



