import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import traceback
import inspect
import os
import sys
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.client import Config
from boto3.s3.transfer import S3Transfer

os.environ['HTTP_PROXY'] = 'http://proxy-usvn.aws.novartis.net:3128'
os.environ['HTTPS_PROXY'] = 'http://proxy-usvn.aws.novartis.net:3128'
os.environ['no_proxy'] = '169.254.169.254,s3.amazonaws.com'

SNAP_SHOT_DETAIL = ""


@dataclass
class AWSConfig:
    """
    AWSConfig Class

    Purpose:
    ----------
    This class represents configuration settings for AWS automation tasks. It includes information
    about AWS regions, bucket names, role ARNs, role sessions, and account IDs.

    Attributes:
    -----------
    regions : List[str]
        A list of AWS regions where operations will be performed.
    today_date : str
        The current date in 'YYYY-MM-DD' format, used for generating timestamped filenames or reports.
    bucket_name : str
        The name of the S3 bucket where reports or files will be stored.
    file_name : str
        The name of the file to be used for storing snapshot details.
    role_arns : List[str]
        A list of AWS IAM role ARNs (Amazon Resource Names) that will be assumed for various operations.
    role_sessions : List[str]
        A list of session names associated with the IAM roles for context-specific sessions.
    account_ids : List[str]
        A list of AWS account IDs associated with the roles and resources being managed.
    """

    regions: List[str] = field(default_factory=lambda: ['us-east-1', 'eu-west-1'])
    today_date: str = field(default_factory=lambda: str(datetime.now().date()))
    bucket_name: str = "novartisrccgbusnvawsassets001"
    file_name: str = "Snapshot_details.txt"
    role_arns: List[str] = field(default_factory=lambda: [
        'arn:aws:iam::128010802554:role/RRCC_AWS_EC2OPSL3',
        'arn:aws:iam::866919043554:role/RRCC_AWS_EC2OPSL3',
        'arn:aws:iam::304512965277:role/RRCC_AWS_EC2OPSL3',
        'arn:aws:iam::720243969453:role/RRCC_AWS_EC2OPSL3',
        'arn:aws:iam::366103429990:role/RRCC_AWS_EC2OPSL3',
        'arn:aws:iam::782671389447:role/RRCC_AWS_EC2OPSL3',
        'arn:aws:iam::132910123013:role/RRCC_AWS_EC2OPSL3',
        'arn:aws:iam::714287346229:role/RRCC_AWS_EC2OPSL3'
    ])
    role_sessions: List[str] = field(default_factory=lambda: [
        'RSA_AWS_EC2OPSL3',
        'RSB_AWS_EC2OPSL3',
        'RCC_AWS_EC2OPSL3',
        'RSID_AWS_EC2OPSL3',
        'BST_AWS_EC2OPSL3',
        'RSI_AWS_EC2OPSL3',
        'DMZ_AWS_EC2OPSL3',
        'RSE_AWS_EC2OPSL3'
    ])
    account_ids: List[str] = field(default_factory=lambda: [
        '128010802554',
        '866919043554',
        '304512965277',
        '720243969453',
        '366103429990',
        '782671389447',
        '132910123013',
        '714287346229'
    ])
    logger: 'CustomLogger' = field(default_factory=lambda: CustomLogger())

    def __post_init__(self):
        """
        Post-initialization checks or operations.
        """
        # Ensure that the number of roles, sessions, and account IDs match
        if not (len(self.role_arns) == len(self.role_sessions) == len(self.account_ids)):
            raise AWSAutomationError("The length of role ARNs, role sessions, and account IDs must be the same.")

        # Additional initialization logic can be added here if needed
        # For example, validating AWS region names or bucket names
        print(f"Configuration initialized for {len(self.regions)} regions.")
        # self.logger.log_info(f"Configuration initialized for {len(self.regions)} regions.")


class AWSAutomationError(Exception):
    """
    AWSAutomationError Class

    Purpose:
    ----------
    A custom exception class for AWS automation errors. This class extends the base `Exception` class
    to provide more specific error handling for operations within AWS.

    Usage:
    ------
    Raise this exception in cases where operations specific to AWS automation fail, providing
    a clear and consistent error message along with the exact error and line number.
    """

    def __init__(self, message: str, original_exception: Exception = None):
        """
        Initializes the AWSAutomationError class with a message and an optional original exception.

        Parameters:
        -----------
        message : str
            The error message to be logged.
        original_exception : Exception, optional
            The original exception that caused this error (default is None).
        """
        super().__init__(message)
        self.original_exception = original_exception
        self.error_trace = self._get_error_trace()

    def _get_error_trace(self) -> str:
        """
        Captures the traceback and the line number of the error.

        Returns:
        --------
        str
            A formatted string with the error message, traceback, and line number.
        """
        tb_str = traceback.format_exception_only(type(self.original_exception),
                                                 self.original_exception) if self.original_exception else ""
        frame = inspect.currentframe().f_back
        line_number = frame.f_lineno if frame else "unknown"
        return f"Error occurred at line {line_number}: {self.args[0]} - Traceback: {''.join(tb_str)}"

    def __str__(self):
        """
        Provides a string representation of the AWSAutomationError, including the traceback information.

        Returns:
        --------
        str
            The formatted string representation of the error.
        """
        return self.error_trace


class CustomLogger:
    """
    CustomLogger Class

    Purpose:
    ----------
    This class sets up a custom logger to log information, warnings, errors, and critical issues
    to both console and a log file.

    Usage:
    ------
    Use this logger for consistent logging throughout your AWS automation scripts.
    """

    def __init__(self, name: str = 'AWSAutomationLogger', log_file: str = 'aws_automation.log'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def log_info(self, message: str) -> None:
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        self.logger.error(message)

    def log_critical(self, message: str) -> None:
        self.logger.critical(message)


@dataclass
class AWSSnapshot:
    """
    AWSSnapshot Dataclass

    Purpose:
    ----------
    Represents an AWS EC2 Snapshot with its relevant attributes.

    Usage:
    ------
    Use this dataclass to manage and store snapshot details in an efficient manner.
    """
    snapshot_id: str
    volume_id: str
    state: str
    progress: str
    owner_id: str
    start_time: str
    encrypted: bool
    description: str
    tags: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        encrypted_status = "Encrypted" if self.encrypted else "Not Encrypted"
        return (
            f"{self.snapshot_id}|{self.volume_id}|{self.state}|{self.progress}|"
            f"{self.owner_id}|{self.start_time}|{encrypted_status}|{self.description}|"
            f"{self.tags.get('Name', 'null')}|{self.tags.get('Owner', 'null')}|"
            f"{self.tags.get('CostCenter', 'null')}|{self.tags.get('ClarityID', 'null')}|"
            f"{self.tags.get('Environment', 'null')}|{self.tags.get('APPType', 'null')}|"
            f"{self.tags.get('OSType', 'null')}|{self.tags.get('BillingContact', 'null')}|"
            f"{self.tags.get('InstanceState', 'null')}"
        )


class AWSSnapshotManager:
    """
    AWSSnapshotManager Class

    Purpose:
    ----------
    This class handles AWS EC2 snapshot operations asynchronously. It uses `boto3` to interact with AWS
    and includes custom logging and error handling.

    Usage:
    ------
    Use this class to automate AWS snapshot management tasks, such as retrieving and processing
    snapshots across different AWS accounts and regions.

    Attributes:
    -----------
    __slots__ : tuple
        Limits the attributes that can be set on an instance, optimizing memory usage.

    logger : CustomLogger
        Instance of the custom logger for logging.

    session : boto3.Session
        The boto3 session used for AWS operations.

    Methods:
    --------
    assume_role(role_arn: str, role_session_name: str) -> None:
        Assumes an AWS IAM role and stores the credentials.

    create_session() -> boto3.Session:
        Creates a boto3 session using the assumed role credentials.

    fetch_snapshots(region: str, owner_id: str) -> List[AWSSnapshot]:
        Fetches EC2 snapshots in a given region and owner account.

    async save_snapshots_to_s3(bucket_name: str, file_name: str, snapshots: List[AWSSnapshot]) -> None:
        Saves the snapshot details to an S3 bucket asynchronously.
    """

    __slots__ = ['logger', 'session', 'aws_config']

    def __init__(self, logger: CustomLogger, aws_config: AWSConfig):
        self.logger = logger
        self.aws_config = aws_config
        self.session: Optional[boto3.Session] = None

    def assume_role(self, role_arn: str, index: int) -> None:
        """
        Assumes an AWS IAM role to gain temporary credentials.

        Parameters:
        -----------
        role_arn : str
            The ARN of the role to assume.
        """
        try:
            client = boto3.client('sts')
            session_name = f"{self.aws_config.role_sessions[index]}-{uuid.uuid4()}"
            response = client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=3600
            )
            credentials = response['Credentials']
            self.session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            # self.logger.log_info(f"Assumed role {role_arn} successfully with session {session_name}.")

            for region in self.aws_config.regions:
                # Fetch snapshots
                snapshots = self.fetch_snapshots(region, self.aws_config.account_ids[index])

        except (ClientError, BotoCoreError) as e:
            self.logger.log_critical(f"Failed to assume role {role_arn}: {e}")
            raise AWSAutomationError("Error assuming AWS IAM role", e)

    def read_snapshot(self, acc_id: str, region: str, access_key: str, sec_key: str, sec_token: str) -> None:
        """
        Reads and prints snapshot details for a given AWS account and region.

        Parameters:
        -----------
        acc_id : str
            The AWS account ID.
        region : str
            The AWS region name.
        access_key : str
            AWS access key.
        sec_key : str
            AWS secret access key.
        sec_token : str
            AWS session token.
        """
        try:
            client = boto3.client('ec2', region_name=region,
                                  aws_access_key_id=access_key,
                                  aws_secret_access_key=sec_key,
                                  aws_session_token=sec_token)

            paginator = client.get_paginator('describe_snapshots')
            page_iterator = paginator.paginate(OwnerIds=[acc_id], MaxResults=500)

            for page in page_iterator:
                snap_details = page['Snapshots']
                for snap in snap_details:
                    snap_id = snap['SnapshotId']
                    snap_tags = snap.get('Tags', [])
                    self.get_keys(snap_tags)
                    launch_time = snap['StartTime'].strftime("%Y-%m-%d %H:%M:%S")
                    encrypted_status = 'Encrypted' if snap['Encrypted'] else 'Not Encrypted'
                    details = (f"{snap['SnapshotId']}|{snap['VolumeId']}|{snap['State']}|{snap['Progress']}|"
                               f"{snap['OwnerId']}|{launch_time}|{encrypted_status}|{snap['Description']}|"
                               f"{self.k['Name']}|{self.k['Owner']}|{self.k['CostCenter']}|{self.k['ClarityID']}|"
                               f"{self.k['Environment']}|{self.k['APPType']}|{self.k['OSType']}|{self.k['BillingContact']}|"
                               f"{self.k['InstanceState']}")
                    print(details)
                    self.logger.log_info(details)

        except Exception as e:
            error_message = f"Error reading snapshot for account {acc_id} in region {region}: {str(e)}"
            self.logger.log_error(error_message)
            raise AWSAutomationError(error_message, e)

    def get_keys(self, tags: List[dict]) -> None:
        """
        Processes snapshot tags and updates internal dictionary with tag values.

        Parameters:
        -----------
        tags : List[dict]
            List of tag dictionaries from AWS snapshots.
        """
        self.k = {key: "null" for key in
                  ["Name", "Owner", "CostCenter", "ClarityID", "Environment", "APPType", "OSType", "BillingContact",
                   "InstanceState"]}
        for tag in tags:
            if tag['Key'] in self.k:
                self.k[tag['Key']] = tag['Value']

    def fetch_snapshots(self, region: str, owner_id: str) -> List[AWSSnapshot]:
        """
        Fetches EC2 snapshots for a given owner in a specified region.

        Parameters:
        -----------
        region : str
            The AWS region to search for snapshots.
        owner_id : str
            The AWS account ID of the snapshot owner.

        Returns:
        --------
        List[AWSSnapshot]
            A list of AWSSnapshot instances representing the snapshots found.
        """
        global SNAP_SHOT_DETAIL
        if not self.session:
            raise AWSAutomationError("AWS session has not been initialized. Please assume a role first.")

        snapshots = []
        try:
            client = self.session.client('ec2', region_name=region)
            paginator = client.get_paginator('describe_snapshots')
            page_iterator = paginator.paginate(OwnerIds=[owner_id])

            for page in page_iterator:
                for snap in page['Snapshots']:
                    tags = {tag['Key']: tag['Value'] for tag in snap.get('Tags', [])}
                    snapshot = AWSSnapshot(
                        snapshot_id=snap['SnapshotId'],
                        volume_id=snap['VolumeId'],
                        state=snap['State'],
                        progress=snap['Progress'],
                        owner_id=snap['OwnerId'],
                        start_time=snap['StartTime'].strftime("%Y-%m-%d %H:%M:%S"),
                        encrypted=snap['Encrypted'],
                        description=snap['Description'],
                        tags=tags
                    )
                    # snapshots.append(snapshot)
                    SNAP_SHOT_DETAIL = SNAP_SHOT_DETAIL + str(snapshot) + "\n"
                    # self.logger.log_info(f"Fetched snapshot {snapshot.snapshot_id} from {region}.")
        except (ClientError, BotoCoreError) as e:
            self.logger.log_critical(f"Failed to fetch snapshots: {e}")
            # raise AWSAutomationError("Error fetching AWS snapshots", e)
        return snapshots

    async def save_snapshots_to_s3(self, bucket_name: str, file_name: str, snapshots: List[AWSSnapshot]) -> None:
        """
        Asynchronously saves snapshot details to an S3 bucket.

        Parameters:
        -----------
        bucket_name : str
            The name of the S3 bucket.
        file_name : str
            The name of the file to be created in the bucket.
        snapshots : List[AWSSnapshot]
            A list of snapshots to save.
        """
        if not self.session:
            raise AWSAutomationError("AWS session has not been initialized. Please assume a role first.")

        try:
            s3_client = self.session.client('s3')
            snapshot_data = "\n".join([str(snapshot.__dict__) for snapshot in snapshots])
            await asyncio.sleep(1)  # Simulate asynchronous delay

            s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=snapshot_data)
            # self.logger.log_info(f"Snapshot data saved to S3 bucket '{bucket_name}' as '{file_name}'.")
        except (ClientError, BotoCoreError) as e:
            self.logger.log_critical(f"Failed to save snapshot data to S3: {e}")
            raise AWSAutomationError("Error saving snapshot data to S3", e)


# Example usage of the classes
async def main():
    logger = CustomLogger()

    # # Create an instance of AWSConfig with default values
    aws_config = AWSConfig()
    snapshot_manager = AWSSnapshotManager(logger, aws_config)

    for index, arn in enumerate(aws_config.role_arns):
        # Assume role
        snapshot_manager.assume_role(arn, index)
    else:
        global SNAP_SHOT_DETAIL
        # Specify the file name
        file_name = "Snapshot_details.txt"

        # Open the file in write mode and write the contents of SNAP_SHOT_DETAIL
        with open(file_name, 'w') as file:
            file.write(SNAP_SHOT_DETAIL)

        print(f"Snapshot details have been written to {file_name}")

    # Save snapshots to S3
    # await snapshot_manager.save_snapshots_to_s3('your-bucket-name', 'snapshots_data.txt', snapshots)


# Running the asynchronous main function
if __name__ == "__main__":
    # For Python 3.6 and earlier
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
