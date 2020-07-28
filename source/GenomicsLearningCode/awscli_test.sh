#!/bin/bash -e

export AWS_DEFAULT_OUTPUT=text

project_name=${PROJECT_NAME:-GenomicsLearning}

resource_prefix=${project_name}

resource_prefix_lowercase=$(echo ${resource_prefix} | tr '[:upper:]' '[:lower:]')

process_data_job="${resource_prefix_lowercase}-create-trainingset"

aws glue get-job --job-name ${process_data_job}

printf "Test:Job exists\n"