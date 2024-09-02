#!/usr/bin/python3

import boto3
from datetime import datetime
import os
import sys
from botocore.client import Config
from boto3.s3.transfer import S3Transfer

client = boto3.client('sts')

k={}
regions          = ['us-east-1','eu-west-1']
today_date   = str(datetime.now().date())
bucket_name  = "novartisrccgbusnvawsassets001"
file_name    = "Volume_details.txt"

ROLE_ARN         = ['arn:aws:iam::128010802554:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::866919043554:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::304512965277:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::720243969453:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::366103429990:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::782671389447:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::132910123013:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::714287346229:role/RRCC_AWS_EC2OPSL3','arn:aws:iam::675512936957:role/RRCC_AWS_EC2OPSL3']
ROLE_SESSION = ['RSA_AWS_EC2OPSL3','RSB_AWS_EC2OPSL3','RCC_AWS_EC2OPSL3','RSID_AWS_EC2OPSL3','BST_AWS_EC2OPSL3','RSI_AWS_EC2OPSL3','DMZ_AWS_EC2OPSL3','RSE_AWS_EC2OPSL3','BCK_AWS_EC2OPSL3']
Account_ID       = ['128010802554','866919043554','304512965277','720243969453','366103429990','782671389447','132910123013','714287346229','675512936957']


def get_keys(data):
    keys = ['Name',"Owner","CostCenter","ClarityID","Environment","APPType","OSType","BillingContact","InstanceState"]
    for i in keys:
        k[i] = "null"
    for item in data:
        if item['Key'] in keys:
            k[item['Key']] = item['Value']

def readVolume(acc_id,region,Access_key,Sec_key,Sec_token):
        try:
                tag_key = []
                temp = {}
                client = boto3.client('ec2',region_name=region,
                        aws_access_key_id=Access_key,
                        aws_secret_access_key=Sec_key,
                        aws_session_token=Sec_token,
                )
                vol_response = client.describe_volumes()['Volumes']
                for vol in vol_response:
                        vol_id = vol['VolumeId']
                        response = client.describe_tags(
                                Filters=[
                                        {
                                                'Name': 'resource-id',
                                                'Values': [
                                                        vol_id,
                                                ],
                                        },
                                ],
                        )
                        attachments = vol['Attachments']
                        for attachment in attachments:
                                inst_id = attachment['InstanceId']
                                re = client.describe_instances(
                                        InstanceIds=[
                                                inst_id,
                                        ],
                                )
                                #print (re)
                                own_id = re['Reservations'][0]['OwnerId']
                                att_device = attachment['Device']
                                val_tags = response['Tags']
                                tag_key.append(temp)
                                get_keys(val_tags)
                                Vol_size1 = vol['Size']
                                Vol_size = str(Vol_size1)
                                if vol['Encrypted'] == False:
                                        Encrypted_Status = 'Not Encrypted'
                                else:
                                        Encrypted_Status = 'Encrypted'
                                print (str(vol['VolumeId']+"|"+vol['AvailabilityZone']+"|"+vol['State']+"|"+vol['VolumeType']+"|"+Vol_size+"|"+Encrypted_Status+"|"+inst_id+"|"+own_id+"|"+att_device+"|"+vol['CreateTime'].strftime("%Y-%m-%d %H:%M:%S")+"|"+k['Name']+"|"+k["Owner"]+"|"+k["CostCenter"]+"|"+k["ClarityID"]+"|"+k["Environment"]+"|"+k["APPType"]+"|"+k["OSType"]+"|"+k["BillingContact"]+"|"+k["InstanceState"]))

        except (Exception, error):
                print("Error"+ str(error))

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
                        readVolume(acc_id,region,Access_key,Sec_key,Sec_token)
        except (Exception, error):
                print("Error"+ str(error))

def uploadFile():
        try:
                s3_upload = boto3.client('s3',region_name='us-east-1',config=Config(signature_version='s3v4'))
                s3_upload.upload_file(file_name, bucket_name, "Volume-Details/"+file_name,ExtraArgs={"ServerSideEncryption":"aws:kms"})



        except (Exception, error):
                print("Error"+ str(error))

def generateVolumeReport():
        try:
                length = len(ROLE_ARN)

                orig_stdout = sys.stdout
                f = open(file_name,'w')
                sys.stdout = f

                for i in range(length):
                        readROLE(i)

                sys.stdout = orig_stdout
                f.close()
                print ("Upload the file to S3 bucket")
                uploadFile()
        except (Exception, error):
                print("Error"+ str(error))

generateVolumeReport()


print ("done")
