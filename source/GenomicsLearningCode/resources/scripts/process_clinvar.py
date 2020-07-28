###############################################################################
#  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.    #
#                                                                             #
#  Licensed under the Apache License, Version 2.0 (the "License").            #
#  You may not use this file except in compliance with the License.
#  A copy of the License is located at                                        #
#                                                                             #
#      http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                             #
#  or in the "license" file accompanying this file. This file is distributed  #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express #
#  or implied. See the License for the specific language governing permissions#
#  and limitations under the License.                                         #
###############################################################################

import gzip, re
import pandas as pd
import csv
import sys
from awsglue.utils import getResolvedOptions
import boto3

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')

args = getResolvedOptions(sys.argv,
                          ['input_bucket', 'clinvar_input_key', 'clinvar_annotated_input_key', 'output_bucket',
                           'output_key'])


def download_to_local(filename):
    new_filename = filename.split('/')[-1]
    s3_resource.meta.client.download_file(args['input_bucket'], filename, '/tmp/' + new_filename)
    return new_filename


def list_to_dict(l):
    """Convert list to dict."""
    return {k: v for k, v in (x.split("=") for x in l)}


fieldnames = [
    "CHROM",
    "POS",
    "REF",
    "ALT",
    "AF_ESP",
    "AF_EXAC",
    "AF_TGP",
    "CLNDISDB",
    "CLNDISDBINCL",
    "CLNDN",
    "CLNDNINCL",
    "CLNHGVS",
    "CLNSIGINCL",
    "CLNVC",
    "CLNVI",
    "MC",
    "ORIGIN",
    "SSR",
    "CLASS",
    "Allele",
    "Consequence",
    "IMPACT",
    "SYMBOL",
    "Feature_type",
    "Feature",
    "BIOTYPE",
    "EXON",
    "INTRON",
    "cDNA_position",
    "CDS_position",
    "Protein_position",
    "Amino_acids",
    "Codons",
    "DISTANCE",
    "STRAND",
    "BAM_EDIT",
    "SIFT",
    "PolyPhen",
    "MOTIF_NAME",
    "MOTIF_POS",
    "HIGH_INF_POS",
    "MOTIF_SCORE_CHANGE",
    "LoFtool",
    "CADD_PHRED",
    "CADD_RAW",
    "BLOSUM62",
]

obj = s3.get_object(Bucket=args['input_bucket'], Key=args['clinvar_input_key'])
cv_columns = {}
with gzip.GzipFile(fileobj=obj['Body'], mode='rb') as f:
    for metaline in f:
        if metaline.startswith(b'##INFO'):
            colname = re.search(b'ID=(\w+),', metaline.strip(b'#\n'))
            coldesc = re.search(b'.*Description=(.*)>', metaline.strip(b'#\n'))
            cv_columns[colname.group(1)] = coldesc.group(1).strip(b'"')

# read clinvar vcf
obj = s3.get_object(Bucket=args['input_bucket'], Key=args['clinvar_input_key'])
with gzip.GzipFile(fileobj=obj['Body'], mode='rb') as f:
    cv_df = pd.read_csv(f, sep='\t', comment='#', header=None, usecols=[0, 1, 2, 3, 4, 7], dtype={0: object})

# convert dictionaries to columns
cv_df = pd.concat(
    [
        cv_df.drop([7], axis=1),
        cv_df[7].str.split(";").apply(list_to_dict).apply(pd.Series),
    ],
    axis=1,
)
# rename columns
cv_df.rename(columns={0: "CHROM", 1: "POS", 2: "ID", 3: "REF", 4: "ALT"}, inplace=True)

# drop columns we know we won't need
cv_df = cv_df.drop(columns=["CHROM", "POS", "REF", "ALT"])

# assign classes
cv_df["CLASS"] = 0
cv_df.loc[cv_df["CLNSIGCONF"].notnull(), "CLASS"] = 1

# convert NaN to 0 where allele frequencies are null
cv_df[["AF_ESP", "AF_EXAC", "AF_TGP"]] = cv_df[["AF_ESP", "AF_EXAC", "AF_TGP"]].fillna(
    0
)

# select variants that have beeen submitted by multiple organizations.
cv_df = cv_df.loc[
    cv_df["CLNREVSTAT"].isin(
        [
            "criteria_provided,_multiple_submitters,_no_conflicts",
            "criteria_provided,_conflicting_interpretations",
        ]
    )
]

# Reduce the size of the dataset below
cv_df.drop(columns=["ALLELEID", "RS", "DBVARID"], inplace=True)
# drop columns that would reveal class
cv_df.drop(columns=["CLNSIG", "CLNSIGCONF", "CLNREVSTAT"], inplace=True)
# drop this redundant columns
cv_df.drop(columns=["CLNVCSO", "GENEINFO"], inplace=True)

# dictionary to map ID to clinvar annotations
clinvar_annotations = cv_df.set_index("ID")[
    [col for col in cv_df.columns if col in fieldnames]
].to_dict(orient="index")

# open the output file
outfile = "/tmp/clinvar_conflicting.csv"
with open(outfile, "w") as fout:
    dw = csv.DictWriter(
        fout, delimiter=",", fieldnames=fieldnames, extrasaction="ignore"
    )
    dw.writeheader()
    # read the VEP-annotated vcf file line-by-line
    filename = download_to_local(args['clinvar_annotated_input_key'])
    filename = "/tmp/" + filename
    with gzip.GzipFile(filename, mode='rb') as f:
        for line in f:
            line = line.decode("utf-8")
            if line.startswith("##INFO=<ID=CSQ"):
                m = re.search(r'.*Format: (.*)">', line)
                cols = m.group(1).split("|")
                continue

            if line.startswith("#"):
                continue
            record = line.split("\t")
            (
                chromosome,
                position,
                clinvar_id,
                reference_base,
                alternate_base,
                qual,
                filter_,
                info,
            ) = record
            info_field = info.strip("\n").split(";")

            # to lookup in clivnar_annotaitons
            clinvar_id = int(clinvar_id)

            # only keep the variants that have been evaluated by multiple submitters
            if clinvar_id in clinvar_annotations:
                # initialize a dictionary to hold all the VEP annotation data
                annotation_data = {column: None for column in cols}
                annotation_data.update(clinvar_annotations[clinvar_id])
                # fields directly from the vcf
                annotation_data["CHROM"] = str(chromosome)
                annotation_data["POS"] = position
                annotation_data["REF"] = reference_base
                annotation_data["ALT"] = alternate_base

                for annotations in info_field:
                    column, value = annotations.split("=")

                    if column == "CSQ":
                        for csq_column, csq_value in zip(cols, value.split("|")):
                            annotation_data[csq_column] = csq_value
                        continue

                    annotation_data[column] = value
                dw.writerow(annotation_data)

s3_resource.meta.client.upload_file(outfile, args['output_bucket'], args['output_key'])