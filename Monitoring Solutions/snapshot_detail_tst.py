import os
import boto3
import sys
from datetime import datetime
from botocore.client import Config



class SnapshotReporter:
    def __init__(self):
        # Set environment variables for proxies
        os.environ['HTTP_PROXY'] = 'http://proxy-usvn.aws.novartis.net:3128'
        os.environ['HTTPS_PROXY'] = 'http://proxy-usvn.aws.novartis.net:3128'
        os.environ['no_proxy'] = '169.254.169.254,s3.amazonaws.com'

        # Initialize necessary variables
        self.regions = ['us-east-1', 'eu-west-1']
        self.today_date = str(datetime.now().date())
        self.bucket_name = "novartisrccgbusnvawsassets001"
        self.file_name = "Snapshot_details.txt"
        self.role_arn = [
            'arn:aws:iam::128010802554:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::866919043554:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::304512965277:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::720243969453:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::366103429990:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::782671389447:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::132910123013:role/RRCC_AWS_EC2OPSL3',
            'arn:aws:iam::714287346229:role/RRCC_AWS_EC2OPSL3'
        ]
        self.role_session = [
            'RSA_AWS_EC2OPSL3',
            'RSB_AWS_EC2OPSL3',
            'RCC_AWS_EC2OPSL3',
            'RSID_AWS_EC2OPSL3',
            'BST_AWS_EC2OPSL3',
            'RSI_AWS_EC2OPSL3',
            'DMZ_AWS_EC2OPSL3',
            'RSE_AWS_EC2OPSL3'
        ]
        self.account_id = [
            '128010802554',
            '866919043554',
            '304512965277',
            '720243969453',
            '366103429990',
            '782671389447',
            '132910123013',
            '714287346229'
        ]

    def get_keys(self, data):
        keys = ['Name', "Owner", "CostCenter", "ClarityID", "Environment", "APPType", "OSType", "BillingContact", "InstanceState"]
        k = {key: "null" for key in keys}
        for item in data:
            if item['Key'] in keys:
                k[item['Key']] = item['Value']
        return k

    def read_snapshot(self, acc_id, region, access_key, sec_key, sec_token):
        try:
            client = boto3.client(
                'ec2',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=sec_key,
                aws_session_token=sec_token
            )
            paginator = client.get_paginator('describe_snapshots')
            page_iterator = paginator.paginate(OwnerIds=[acc_id], MaxResults=500)

            for page in page_iterator:
                snap_details = page['Snapshots']
                for snap in snap_details:
                    # snap_id = snap['SnapshotId']
                    if 'Tags' in snap:
                        snap_tags = snap['Tags']
                        k = self.get_keys(snap_tags)
                        launch_time = snap['StartTime'].strftime("%Y-%m-%d %H:%M:%S")
                        encrypted_status = 'Encrypted' if snap['Encrypted'] else 'Not Encrypted'
                        # SNAP_SHOT_DETAIL += f"{snap['SnapshotId']}|{snap['VolumeId']}|{snap['State']}|{snap['Progress']}|{snap['OwnerId']}|{launch_time}|{encrypted_status}|{snap['Description']}|{k['Name']}|{k['Owner']}|{k['CostCenter']}|{k['ClarityID']}|{k['Environment']}|{k['APPType']}|{k['OSType']}|{k['Environment']}|{k['APPType']}|{k['OSType']}\n"

                        print(f"{snap['SnapshotId']}|{snap['VolumeId']}|{snap['State']}|{snap['Progress']}|{snap['OwnerId']}|{launch_time}|{encrypted_status}|{snap['Description']}|{k['Name']}|{k['Owner']}|{k['CostCenter']}|{k['ClarityID']}|{k['Environment']}|{k['APPType']}|{k['OSType']}|{k['Environment']}|{k['APPType']}|{k['OSType']}")
                    else:
                        # print(snap)
                        launch_time = snap['StartTime'].strftime("%Y-%m-%d %H:%M:%S")
                        encrypted_status = 'Encrypted' if snap['Encrypted'] else 'Not Encrypted'
                        print(f"{snap['SnapshotId']}|{snap['VolumeId']}|{snap['State']}|{snap['Progress']}|{snap['OwnerId']}|{launch_time}|{encrypted_status}|{snap['Description']}|null|null|null|null|null|null|null|null|null|null")
                        # SNAP_SHOT_DETAIL += f"{snap['SnapshotId']}|null|null|null|null|null|null|null|null|null|null|null|null|null|null|null|null|null\n"
        except Exception as error:
            print(f"Error: {error}")

    def assume_role_and_read_snapshots(self, i):
        try:
            sts_client = boto3.client('sts')
            response = sts_client.assume_role(
                RoleArn=self.role_arn[i],
                RoleSessionName=self.role_session[i],
                DurationSeconds=43200
            )
            access_key = response['Credentials']['AccessKeyId']
            sec_key = response['Credentials']['SecretAccessKey']
            sec_token = response['Credentials']['SessionToken']
            acc_id = self.account_id[i]
            for region in self.regions:
                self.read_snapshot(acc_id, region, access_key, sec_key, sec_token)
        except Exception as error:
            print(f"Error: {error}")

    def upload_file(self):
        try:
            s3_upload = boto3.client('s3', region_name='us-east-1', config=Config(signature_version='s3v4'))
            s3_upload.upload_file(
                self.file_name,
                self.bucket_name,
                f"Snapshot-Details/{self.file_name}",
                ExtraArgs={"ServerSideEncryption": "aws:kms"}
            )
        except Exception as error:
            print(f"Error: {error}")

    def generate_snapshot_report(self):
        try:
            # global SNAP_SHOT_DETAIL
            length = len(self.role_arn)
            # for i in range(length):
            #     self.assume_role_and_read_snapshots(i)


            orig_stdout = sys.stdout
            with open(self.file_name, 'w') as f:
                sys.stdout = f
                for i in range(length):
                    self.assume_role_and_read_snapshots(i)
                sys.stdout = orig_stdout

            # print("Upload the file to S3 bucket")
            # self.upload_file()
            # Write the SNAP_SHOT_DETAIL to a file
            # file_name = "Snapshot_details.txt"
            # with open(file_name, "w") as file:
            #     file.write(SNAP_SHOT_DETAIL)

            print(f"Snapshot details saved to {self.file_name}")
        except Exception as error:
            print(f"Error: {error}")

if __name__ == "__main__":
    reporter = SnapshotReporter()
    reporter.generate_snapshot_report()
    print("done")