#!/usr/bin/python3
## This script will list the Instance details
import boto3
from datetime import datetime
import os
import sys
import shlex
from botocore.client import Config
from boto3.s3.transfer import S3Transfer

client = boto3.client("sts")


k = {}
regions = ["us-east-1", "eu-west-1", "eu-central-1", "us-west-2", "ap-northeast-1"]
today_date = str(datetime.now().date())
bucket_name = "novartisrccgbusnvawsassets001"
file_name = "Instance_details.txt"

ROLE_ARN = [
    "arn:aws:iam::128010802554:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::866919043554:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::304512965277:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::720243969453:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::366103429990:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::782671389447:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::132910123013:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::714287346229:role/RRCC_AWS_EC2OPSL3",
    "arn:aws:iam::675512936957:role/RRCC_AWS_EC2OPSL3",
]
ROLE_SESSION = [
    "RSA_AWS_EC2OPSL3",
    "RSB_AWS_EC2OPSL3",
    "RCC_AWS_EC2OPSL3",
    "RSID_AWS_EC2OPSL3",
    "BST_AWS_EC2OPSL3",
    "RSI_AWS_EC2OPSL3",
    "DMZ_AWS_EC2OPSL3",
    "RSE_AWS_EC2OPSL3",
    "BCK_AWS_EC2OPSL3",
]
Account_ID = [
    "128010802554",
    "866919043554",
    "304512965277",
    "720243969453",
    "366103429990",
    "782671389447",
    "132910123013",
    "714287346229",
    "675512936957",
]


def get_keys(data):

    keys = [
        "Name",
        "Owner",
        "CostCenter",
        "ClarityID",
        "Environment",
        "APPType",
        "OSType",
        "BillingContact",
        "InstanceState",
        "Stack",
        "ServerType",
        "BackupID",
        "SchedulerID",
        "TerminationDate",
        "Compliance",
        "ExceptionList",
        "ADJoined",
        "CreationDate",
        "ChargeID",
        "SupportScope",
        "Day2Operation",
        "aws:cloudformation:logical-id",
        "aws:cloudformation:stack-name",
        "aws:autoscaling:groupName",
        "aws:ec2:fleet-id",
        "aws:ec2launchtemplate:id",
        "aws:ec2launchtemplate:version",
        "aws:eks:cluster-name",
        "aws:elasticmapreduce:instance-group-role",
        "aws:elasticmapreduce:job-flow-id",
        "Component",
        "RITM",
        "ServiceNowCatalog",
        "ServiceNowInstanceName",
        "vmw:provisioning:blueprint",
        "vmw:provisioning:blueprintResourceName",
        "vmw:provisioning:blueprintVersion",
        "vmw:provisioning:cloudZone",
        "vmw:provisioning:constraints.placement",
        "vmw:provisioning:deployment",
        "vmw:provisioning:flavorMapping",
        "vmw:provisioning:imageMapping",
        "vmw:provisioning:org",
        "vmw:provisioning:project",
        "vmw:provisioning:requester",
        "Purpose",
        "SchedulerID-RITM",
    ]
    # Added Day2Operatiosn key to the list on 17-sept-2021 by Praveen Rayidi
    # keys = ['Name',"Owner","CostCenter","ClarityID","Environment","APPType","OSType","BillingContact","InstanceState","Stack","ServerType","BackupID","SchedulerID","TerminationDate","Compliance","ExceptionList","ADJoined","CreationDate","ChargeID","SupportScope"]
    for i in keys:
        k[i] = "null"
    for item in data:
        if item["Key"] in keys:
            k[item["Key"]] = item["Value"]


def readInstances(region, Access_key, Sec_key, Sec_token):
    try:
        tag_key = []
        temp = {}

        # Grab the account alias value.
        # Below needs to be checked and enabled
        # AccountName = boto3.client("iam").list_account_aliases()["AccountAliases"][0]
        iam_client = boto3.client(
            "iam",
            aws_access_key_id=Access_key,
            aws_secret_access_key=Sec_key,
            aws_session_token=Sec_token,
            region_name="us-east-1",
        )
        AccountName = iam_client.list_account_aliases()["AccountAliases"][0]

        client = boto3.client(
            "ec2",
            region_name=region,
            aws_access_key_id=Access_key,
            aws_secret_access_key=Sec_key,
            aws_session_token=Sec_token,
        )
        response = client.describe_instances()
        values = response["Reservations"]
        for value in values:
            acc_id = value["OwnerId"]
            for details in value["Instances"]:
                if (
                    details["State"]["Name"] == "running"
                    or details["State"]["Name"] == "stopped"
                ):
                    inst_id = details["InstanceId"]
                    response = client.describe_tags(
                        Filters=[
                            {
                                "Name": "resource-id",
                                "Values": [
                                    inst_id,
                                ],
                            },
                        ],
                    )
                    inst_tags = response["Tags"]
                    get_keys(inst_tags)
                    Netword_details = details["NetworkInterfaces"][0]
                    Launch_Time = details["LaunchTime"]
                    Launch_date = Launch_Time.strftime("%Y-%m-%d")
                    Launch_date_Time = Launch_Time.strftime("%Y-%m-%d %H:%M:%S")
                    print(
                        str(
                            details["InstanceId"]
                            + "|"
                            + k["Name"]
                            + "|"
                            + details["InstanceType"]
                            + "|"
                            + details["Placement"]["AvailabilityZone"]
                            + "|"
                            + Netword_details["VpcId"]
                            + "|"
                            + Netword_details["SubnetId"]
                            + "|"
                            + details["PrivateIpAddress"]
                            + "|"
                            + details["State"]["Name"]
                            + "|"
                            + acc_id
                            + "|"
                            + Launch_date_Time
                            + "|"
                            + details["ImageId"]
                            + "|"
                            + k["Owner"]
                            + "|"
                            + k["CostCenter"]
                            + "|"
                            + k["ClarityID"]
                            + "|"
                            + k["Environment"]
                            + "|"
                            + k["APPType"]
                            + "|"
                            + k["OSType"]
                            + "|"
                            + k["BillingContact"]
                            + "|"
                            + k["InstanceState"]
                            + "|"
                            + k["Stack"]
                            + "|"
                            + k["ServerType"]
                            + "|"
                            + k["BackupID"]
                            + "|"
                            + k["SchedulerID"]
                            + "|"
                            + k["TerminationDate"]
                            + "|"
                            + k["Compliance"]
                            + "|"
                            + k["ExceptionList"]
                            + "|"
                            + k["ADJoined"]
                            + "|"
                            + k["CreationDate"]
                            + "|"
                            + k["ChargeID"]
                            + "|"
                            + k["SupportScope"]
                            + "|"
                            + k["Day2Operation"]
                            + "|"
                            + k["aws:cloudformation:logical-id"]
                            + "|"
                            + k["aws:cloudformation:stack-name"]
                            + "|"
                            + k["aws:autoscaling:groupName"]
                            + "|"
                            + k["aws:ec2:fleet-id"]
                            + "|"
                            + k["aws:ec2launchtemplate:id"]
                            + "|"
                            + k["aws:ec2launchtemplate:version"]
                            + "|"
                            + k["aws:eks:cluster-name"]
                            + "|"
                            + k["aws:elasticmapreduce:instance-group-role"]
                            + "|"
                            + k["aws:elasticmapreduce:job-flow-id"]
                            + "|"
                            + k["Component"]
                            + "|"
                            + k["RITM"]
                            + "|"
                            + k["ServiceNowCatalog"]
                            + "|"
                            + k["ServiceNowInstanceName"]
                            + "|"
                            + k["vmw:provisioning:blueprint"]
                            + "|"
                            + k["vmw:provisioning:blueprintResourceName"]
                            + "|"
                            + k["vmw:provisioning:blueprintVersion"]
                            + "|"
                            + k["vmw:provisioning:cloudZone"]
                            + "|"
                            + k["vmw:provisioning:constraints.placement"]
                            + "|"
                            + k["vmw:provisioning:deployment"]
                            + "|"
                            + k["vmw:provisioning:flavorMapping"]
                            + "|"
                            + k["vmw:provisioning:imageMapping"]
                            + "|"
                            + k["vmw:provisioning:org"]
                            + "|"
                            + k["vmw:provisioning:project"]
                            + "|"
                            + k["vmw:provisioning:requester"]
                            + "|"
                            + k["Purpose"]
                            + "|"
                            + k["SchedulerID-RITM"]
                        )
                    )
        # Added Day2operations to the result by Praveen Rayidi on 17-sept-2021
        # print (str(details['InstanceId']+"|"+k['Name']+"|"+details['InstanceType']+"|"+details['Placement']['AvailabilityZone']+"|"+Netword_details['VpcId']+"|"+Netword_details['SubnetId']+"|"+details['PrivateIpAddress']+"|"+details['State']['Name']+"|"+acc_id+"|"+Launch_date_Time+"|"+details['ImageId']+"|"+k["Owner"]+"|"+k["CostCenter"]+"|"+k["ClarityID"]+"|"+k["Environment"]+"|"+k["APPType"]+"|"+k["OSType"]+"|"+k["BillingContact"]+"|"+k["InstanceState"]+"|"+k["Stack"]+"|"+k["ServerType"]+"|"+k["BackupID"]+"|"+k["SchedulerID"]+"|"+k["TerminationDate"]+"|"+k["Compliance"]+"|"+k["ExceptionList"]+"|"+k["ADJoined"]+"|"+k["CreationDate"]+"|"+k["ChargeID"]+"|"+k["SupportScope"]))
    except (Exception, error):
        print("Error in Read Instances" + str(error))


def readROLE(i):
    try:
        response = client.assume_role(
            RoleArn=ROLE_ARN[i], RoleSessionName=ROLE_SESSION[i], DurationSeconds=43200
        )

        Access_key = response["Credentials"]["AccessKeyId"]
        Sec_key = response["Credentials"]["SecretAccessKey"]
        Sec_token = response["Credentials"]["SessionToken"]
        acc_id = Account_ID[i]
        for region in regions:
            readInstances(region, Access_key, Sec_key, Sec_token)
    except (Exception, error):
        print("Error in Read Role" + str(error))


def uploadFile():
    try:
        s3_upload = boto3.client(
            "s3", region_name="us-east-1", config=Config(signature_version="s3v4")
        )
        s3_upload.upload_file(
            file_name,
            bucket_name,
            "Instance-Details/" + file_name,
            ExtraArgs={"ServerSideEncryption": "aws:kms"},
        )

    except (Exception, error):
        print("Errorin UploadFile" + str(error))


def generateInstanceReport():
    try:
        length = len(ROLE_ARN)

        orig_stdout = sys.stdout
        f = open(file_name, "w")
        sys.stdout = f
        # Adding a header to the output by Praveen Rayidi on 17-Sept-2021
        print(
            "InstanceId|Name|InstanceType|AvailabilityZone|VpcId|SubnetId|PrivateIpAddress|State|acc_id|Launch_date_Time|ImageId|Owner|CostCenter|ClarityID|Environment|APPType|OSType|BillingContact|InstanceState|Stack|ServerType|BackupID|SchedulerID|TerminationDate|Compliance|ExceptionList|ADJoined|CreationDate|ChargeID|SupportScope|Day2Operation|aws:cloudformation:logical-id|aws:cloudformation:stack-name|aws:autoscaling:groupName|aws:ec2:fleet-id|aws:ec2launchtemplate:id|aws:ec2launchtemplate:version|aws:eks:cluster-name|aws:elasticmapreduce:instance-group-role|aws:elasticmapreduce:job-flow-id|Component|RITM|ServiceNowCatalog|ServiceNowInstanceName|vmw:provisioning:blueprint|vmw:provisioning:blueprintResourceName|vmw:provisioning:blueprintVersion|vmw:provisioning:cloudZone|vmw:provisioning:constraints.placement|vmw:provisioning:deployment|vmw:provisioning:flavorMapping|vmw:provisioning:imageMapping|vmw:provisioning:org|vmw:provisioning:project|vmw:provisioning:requester|Purpose|SchedulerID-RITM"
        )
        for i in range(length):
            readROLE(i)

        sys.stdout = orig_stdout
        f.close()
        print("Upload the file to S3 bucket")
        uploadFile()
    except (Exception, error):
        print("Error in Report Generation" + str(error))


generateInstanceReport()

print("done")
