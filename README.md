# Deprecation Notice

This AWS Solution has been archived and is no longer maintained by AWS. A new version of the solution is here: [Guidance for Multi-Omics and Multi-Modal Data Integration and Analysis on AWS](https://aws.amazon.com/solutions/guidance/multi-omics-and-multi-modal-data-integration-and-analysis/). To discover other solutions, please visit the [AWS Solutions Library](https://aws.amazon.com/solutions/).

# Genomics Tertiary Analysis and Machine Learning Using Amazon SageMaker

<img src="https://d1.awsstatic.com/Solutions/Solutions%20Category%20Template%20Draft/Solution%20Architecture%20Diagrams/genomics-tertiary-analysis-and-machine-learning-architecture-diagram.102c69721d29289d37ac46615dc602034e69bcc0.png" style="width:75vw">

The Genomics Tertiary Analysis and Machine Learning Using Amazon SageMaker solution creates a scalable environment in AWS to develop machine learning models using genomics data, generate predictions, and evaluate model performance. This solution demonstrates how to 1) automate the preparation of a genomics machine learning training dataset, 2) develop genomics machine learning model training and deployment pipelines and, 3) generate predictions and evaluate model performance using test data.

## Standard deployment

To deploy this solution in your account use the "Launch in the AWS Console" button found on the [solution landing page](https://aws.amazon.com/solutions/implementations/genomics-tertiary-analysis-and-machine-learning-using-amazon-sagemaker/?did=sl_card&trk=sl_card).

We recommend deploying the solution this way for most use cases.

## Customized deployment

A fully customized solution can be deployed for the following use cases:

* Modifying or adding additional resources deployed during installation
* Modifying the "Landing Zone" of the solution - e.g. adding additional artifacts or customizing the "Pipe" CodePipeline

Fully customized solutions need to be self-hosted in your own AWS account, and you will be responsible for any costs incurred in doing so.

To deploy and self-host a fully customized solution use the instructions below.

_Note_: All commands assume a `bash` shell.

### Customize

Clone the repository, and make desired changes

#### File Structure

```
.
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE.txt
├── NOTICE.txt
├── README.md
├── buildspec.yml
├── deploy.sh
├── deployment
│   ├── build-open-source-dist.sh
│   ├── build-s3-dist.sh
│   └── run-unit-tests.sh
└── source
    ├── GenomicsLearningCode
    │   ├── awscli_test.sh
    │   ├── code_cfn.yml
    │   ├── copyresources_buildspec.yml
    │   ├── resources
    │   │   ├── notebooks
    │   │   │   ├── variant_classifier-autopilot.ipynb
    │   │   │   └── variant_predictor.ipynb
    │   │   └── scripts
    │   │       └── process_clinvar.py
    │   └── setup
    │       ├── lambda.py
    │       └── requirements.txt
    ├── GenomicsLearningPipe
    │   └── pipe_cfn.yml
    ├── GenomicsLearningZone
    │   └── zone_cfn.yml
    ├── setup.sh
    ├── setup_cfn.yml
    └── teardown.sh

```

| Path | Description |
| :-   | :-          |
| deployment | Scripts for building and deploying a customized distributable |
| deployment/build-s3-dist.sh | Shell script for packaging distribution assets |
| deployment/run-unit-tests.sh | Shell script for execution unit tests |
| source     | Source code for the solution |
| source/setup_cfn.yaml | CloudFormation template used to install the solution |
| source/GenomicsLearningZone/ | Source code for the solution landing zone - location for common assets and artifacts used by the solution |
| source/GenomicsLearningPipe/ | Source code for the solution deployment pipeline - the CI/CD pipeline that builds and deploys the solution codebase |
| source/GenomicsLearningCode/ | Source code for the solution codebase - source code for the training job and ML notebooks |

### Run unit tests

```bash
cd ./deployment
chmod +x ./run-unit-tests.sh
./run-unit-tests.sh
```

### Build and deploy

#### Create deployment buckets

The solution requires two buckets for deployment:

1. `<bucket-name>` for the solution's primary CloudFormation template
2. `<bucket-name>-<aws_region>` for additional artifacts and assets that the solution requires - these are stored regionally to reduce latency during installation and avoid inter-regional transfer costs

#### Configure and build the distributable

```bash
export DIST_OUTPUT_BUCKET=<bucket-name>
export SOLUTION_NAME=<solution-name>
export VERSION=<version>

chmod +x ./build-s3-dist.sh
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
```

#### Deploy the distributable

_Note:_ you must have the AWS Command Line Interface (CLI) installed for this step. Learn more about the AWS CLI [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html).

```bash
cd ./deployment

# deploy global assets
# this only needs to be done once
aws s3 cp \
    ./global-s3-assets/ s3://<bucket-name>/$SOLUTION_NAME/$VERSION \
    --recursive \
    --acl bucket-owner-full-control

# deploy regional assets
# repeat this step for as many regions as needed
aws s3 cp \
    ./regional-s3-assets/ s3://<bucket-name>-<aws_region>/$SOLUTION_NAME/$VERSION \
    --recursive \
    --acl bucket-owner-full-control
```

### Install the customized solution

The link to the primary CloudFormation template will look something like:

```text
https://<bucket-name>.s3-<region>.amazonaws.com/genomics-tertiary-analysis-and-data-lakes-using-amazon-sagemaker.template
```

Use this link to install the customized solution into your AWS account in a specific region using the [AWS Cloudformation Console](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/template).

---

This solution collects anonymous operational metrics to help AWS improve the
quality of features of the solution. For more information, including how to disable
this capability, please see the [implementation guide](https://docs.aws.amazon.com/solutions/latest/genomics-tertiary-analysis-and-machine-learning-using-amazon-sagemaker/appendix-f.html).

---

Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
