#!/usr/bin/env python3

import os
import json

from aws_cdk import (
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    core
)

NAMING_PREFIX = f'emr-launch-{core.Aws.ACCOUNT_ID}-{core.Aws.REGION}'

app = core.App()
stack = core.Stack(app, 'EmrLaunchExamplesEnvStack', env=core.Environment(
    account=os.environ['CDK_DEFAULT_ACCOUNT'],
    region=os.environ['CDK_DEFAULT_REGION']))

vpc = ec2.Vpc(
        stack, 'EmrLaunchVpc',                    
        cidr="10.104.197.128/25",                                                                                                     
       max_azs=1,                                     
       nat_gateways=1,
       subnet_configuration=[ec2.SubnetConfiguration(name="public", cidr_mask=26, subnet_type=ec2.SubnetType.PUBLIC),
                             ec2.SubnetConfiguration(name="private", cidr_mask=26, subnet_type=ec2.SubnetType.PRIVATE)                   
#                            ec2.SubnetConfiguration(name="private", cidr_mask=26, subnet_type=ec2.SubnetType.ISOLATED)]
] )

logs_bucket = s3.Bucket(
    stack, 'EmrLaunchLogsBucket',
    bucket_name=f'{NAMING_PREFIX}-logs',
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
)
artifacts_bucket = s3.Bucket(
    stack, 'EmrLaunchArtifactsBucket',
    bucket_name=f'{NAMING_PREFIX}-artifacts',
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
)
data_bucket = s3.Bucket(
    stack, 'EmrLaunchDataBucket',
    bucket_name=f'{NAMING_PREFIX}-data',
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
)

external_metastore_secret = secretsmanager.Secret(
    stack, 'EmrLaunchExternalMetastoreSecret',
    secret_name=f'{NAMING_PREFIX}-external-metastore',
    generate_secret_string=secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({
            'javax.jdo.option.ConnectionURL': 'jdbc',
            'javax.jdo.option.ConnectionDriverName': 'mariaDB',
            'javax.jdo.option.ConnectionUserName': 'user',
        }),
        generate_string_key='javax.jdo.option.ConnectionPassword',
    ),
)
kerberos_attributes_secret = secretsmanager.Secret(
    stack, 'EmrLaunchKerberosAttributesSecret',
    secret_name=f'{NAMING_PREFIX}-kerberos-attributes',
    generate_secret_string=secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({
            'Realm': 'EC2.INTERNAL',
        }),
        generate_string_key='KdcAdminPassword',
    ),
)

app.synth()
