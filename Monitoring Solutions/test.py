import os
import boto3
from datetime import datetime
from botocore.client import Config
import threading

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
        self.file_name = "test.txt"
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
        self.lock = threading.Lock()

    def get_keys(self, data):
        keys = ['Name', 'Owner', 'CostCenter', 'ClarityID', 'Environment', 'APPType', 'OSType', 'BillingContact', 'InstanceState']
        k = {key: "null" for key in keys}
        for item in data:
            if item['Key'] in keys:
                k[item['Key']] = item['Value']
        return k

    def read_snapshot(self, acc_id, region, access_key, sec_key, sec_token, thread_id):
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

            thread_file_name = f"{self.file_name}_thread_{thread_id}.txt"
            with open(thread_file_name, 'w') as file_handle:
                for page in page_iterator:
                    snap_details = page['Snapshots']
                    for snap in snap_details:
                        if 'Tags' in snap:
                            snap_tags = snap['Tags']
                            k = self.get_keys(snap_tags)
                            launch_time = snap['StartTime'].strftime("%Y-%m-%d %H:%M:%S")
                            encrypted_status = 'Encrypted' if snap['Encrypted'] else 'Not Encrypted'
                            data_line = (
                                f"{snap['SnapshotId']}|{snap['VolumeId']}|{snap['State']}|{snap['Progress']}|"
                                f"{snap['OwnerId']}|{launch_time}|{encrypted_status}|{snap['Description']}|{k['Name']}|"
                                f"{k['Owner']}|{k['CostCenter']}|{k['ClarityID']}|{k['Environment']}|{k['APPType']}|"
                                f"{k['OSType']}|{k['BillingContact']}|{k['InstanceState']}\n"
                            )
                        else:
                            launch_time = snap['StartTime'].strftime("%Y-%m-%d %H:%M:%S")
                            encrypted_status = 'Encrypted' if snap['Encrypted'] else 'Not Encrypted'
                            data_line = (
                                f"{snap['SnapshotId']}|{snap['VolumeId']}|{snap['State']}|{snap['Progress']}|"
                                f"{snap['OwnerId']}|{launch_time}|{encrypted_status}|{snap['Description']}|"
                                "null|null|null|null|null|null|null|null\n"
                            )

                        file_handle.write(data_line)
        except Exception as error:
            print(f"Error in read_snapshot for region {region}: {error}")

    def assume_role_and_read_snapshots(self, i, thread_id):
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
                self.read_snapshot(acc_id, region, access_key, sec_key, sec_token, thread_id)

        except Exception as error:
            print(f"Error in assume_role_and_read_snapshots: {error}")

    def generate_snapshot_report(self):
        try:
            threads = []
            for i in range(len(self.role_arn)):
                thread = threading.Thread(target=self.assume_role_and_read_snapshots, args=(i, i))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Combine all thread files into the main file
            with open(self.file_name, 'w') as main_file:
                for i in range(len(self.role_arn)):
                    thread_file_name = f"{self.file_name}_thread_{i}.txt"
                    with open(thread_file_name, 'r') as thread_file:
                        main_file.write(thread_file.read())
                    os.remove(thread_file_name)

            print(f"Snapshot details saved to {self.file_name}")
        except Exception as error:
            print(f"Error in generate_snapshot_report: {error}")

if __name__ == "__main__":
    reporter = SnapshotReporter()
    reporter.generate_snapshot_report()
    print("done")
