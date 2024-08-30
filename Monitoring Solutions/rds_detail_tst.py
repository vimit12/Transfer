#!/usr/bin/python3
### This Script is get the RDS details from All the accounts

import boto3
from datetime import datetime
import os
import sys
from botocore.client import Config
from boto3.s3.transfer import S3Transfer

client = boto3.client('sts')

k = {}
regions = ['us-east-1', 'eu-west-1']
today_date = str(datetime.now().date())
bucket_name = "novartisrccgbusnvawsassets001"
file_name = "RDS_Details.txt"

ROLE_ARN = ['arn:aws:iam::128010802554:role/RRCC_AWS_EC2OPSL3', 'arn:aws:iam::866919043554:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::304512965277:role/RRCC_AWS_EC2OPSL3', 'arn:aws:iam::720243969453:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::366103429990:role/RRCC_AWS_EC2OPSL3', 'arn:aws:iam::782671389447:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::132910123013:role/RRCC_AWS_EC2OPSL3', 'arn:aws:iam::714287346229:role/RRCC_AWS_EC2OPSL3']
ROLE_SESSION = ['RSA_AWS_EC2OPSL3', 'RSB_AWS_EC2OPSL3', 'RCC_AWS_EC2OPSL3', 'RSID_AWS_EC2OPSL3', 'BST_AWS_EC2OPSL3',
                'RSI_AWS_EC2OPSL3', 'DMZ_AWS_EC2OPSL3', 'RSE_AWS_EC2OPSL3']
Account_ID = ['128010802554', '866919043554', '304512965277', '720243969453', '366103429990', '782671389447',
              '132910123013', '714287346229']


def get_keys(data):
    # keys = ["Owner","CostCenter","ClarityID","Environment","APPType","OSType","BillingContact","InstanceState"]
    # Adding other tags to the above list of keys
    keys = ["Owner", "CostCenter", "ClarityID", "Environment", "APPType", "OSType", "BillingContact", "InstanceState",
            "BackupID", "SchedulerID", "TerminationDate", "ExceptionList", "ChargeID", "BackupDR"]
    for i in keys:
        k[i] = "null"
    for item in data:
        if item['Key'] in keys:
            k[item['Key']] = item['Value']


def readRDS(acc_id, region, Access_key, Sec_key, Sec_token):
    try:
        rds_client = boto3.client('rds', region_name=region,
                                  aws_access_key_id=Access_key,
                                  aws_secret_access_key=Sec_key,
                                  aws_session_token=Sec_token
                                  )

        tag_key = []
        temp = {}
        rds_response = rds_client.describe_db_instances()['DBInstances']
        for value in rds_response:
            rds_arn = value['DBInstanceArn']
            endpoint = value.get('Endpoint').get(
                'Address')  # Added DB endpoint as per IAM team Sreekanth request for PAM onboarding/verification purpose
            subnetGroup = value['DBSubnetGroup']
            response = rds_client.list_tags_for_resource(
                ResourceName=rds_arn,
            )
            val_tags = response['TagList']
            get_keys(val_tags)
            sub_id = []
            for inner_sub in subnetGroup['Subnets']:
                sub_id.append(inner_sub['SubnetIdentifier'])
            sub = (",".join(sub_id))
            Launch_Time = value['InstanceCreateTime'].strftime("%Y-%m-%d %H:%M:%S")
            if not 'DBName' in value.keys():
                DBName = "n/a"
            else:
                DBName = value['DBName']

            # print (str(value['DBInstanceIdentifier'] + "|" + DBName + "|"+ value['AvailabilityZone']+ "|"+value['Engine']+ "|"+ value['DBInstanceClass']+ "|"+ subnetGroup['VpcId']+"|"+ sub+"|"+ Launch_Time + "|"+ acc_id+ "|"+ k["Owner"]+"|"+k["CostCenter"]+"|"+k["ClarityID"]+"|"+k["APPType"]+"|"+k["Environment"]+"|"+k["BillingContact"]+"|"+k["InstanceState"]))
            # Adding the newly added tag keys to teh print statement
            print(str(value['DBInstanceIdentifier'] + "|" + DBName + "|" + value['AvailabilityZone'] + "|" + value[
                'Engine'] + "|" + value['DBInstanceClass'] + "|" + endpoint + "|" + subnetGroup[
                          'VpcId'] + "|" + sub + "|" + Launch_Time + "|" + acc_id + "|" + k["Owner"] + "|" + k[
                          "CostCenter"] + "|" + k["ClarityID"] + "|" + k["APPType"] + "|" + k["Environment"] + "|" + k[
                          "BillingContact"] + "|" + k["InstanceState"] + "|" + k["BackupID"] + "|" + k[
                          "SchedulerID"] + "|" + k["TerminationDate"] + "|" + k["ExceptionList"] + "|" + k[
                          "ChargeID"] + "|" + k["BackupDR"]))


    except (Exception, error):
        print("Error" + str(error))


def readROLE(i):
    try:

        response = client.assume_role(
            RoleArn=ROLE_ARN[i],
            RoleSessionName=ROLE_SESSION[i],
            DurationSeconds=43200
        )

        Access_key = response['Credentials']['AccessKeyId']
        Sec_key = response['Credentials']['SecretAccessKey']
        Sec_token = response['Credentials']['SessionToken']
        acc_id = Account_ID[i]

        for region in regions:
            readRDS(acc_id, region, Access_key, Sec_key, Sec_token)
    except (Exception, error):
        print("Error" + str(error))


def uploadFile():
    try:
        s3_upload = boto3.client('s3', region_name='us-east-1', config=Config(signature_version='s3v4'))
        s3_upload.upload_file(file_name, bucket_name, "RDS-Details/" + file_name,
                              ExtraArgs={"ServerSideEncryption": "aws:kms"})



    except (Exception, error):
        print("Error" + str(error))


def generateRDSReport():
    try:
        length = len(ROLE_ARN)

        orig_stdout = sys.stdout
        f = open(file_name, 'w')
        sys.stdout = f

        print(
            "DBInstanceIdentifier|DBName|AvailabilityZone|Engine|DBInstanceClass|Endpoint|VpcId|subnet|Launch_Time|acc_id|Owner|CostCenter|ClarityID|APPType|Environment|BillingContact|InstanceState|BackupID|SchedulerID|TerminationDate|ExceptionList|ChargeID|BackupDR")

        for i in range(length):
            readROLE(i)

        sys.stdout = orig_stdout
        f.close()
        print("Upload the file to S3 bucket")
        uploadFile()
    except (Exception, error):
        print("Error" + str(error))


generateRDSReport()
print("done")