import asyncio
import boto3
import logging
import uuid
from botocore.exceptions import ClientError, BotoCoreError
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import traceback
import inspect
import os
import sys




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

    __slots__ = ['logger', 'session']

    def __init__(self, logger: CustomLogger):
        self.logger = logger
        self.session: Optional[boto3.Session] = None

    def assume_role(self, role_arn: str) -> None:
        """
        Assumes an AWS IAM role to gain temporary credentials.

        Parameters:
        -----------
        role_arn : str
            The ARN of the role to assume.
        """
        try:
            client = boto3.client('sts')
            session_name = f"AWSAutomation-{uuid.uuid4()}"
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
            self.logger.log_info(f"Assumed role {role_arn} successfully with session {session_name}.")
        except (ClientError, BotoCoreError) as e:
            self.logger.log_critical(f"Failed to assume role {role_arn}: {e}")
            raise AWSAutomationError("Error assuming AWS IAM role", e)

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
                    snapshots.append(snapshot)
                    self.logger.log_info(f"Fetched snapshot {snapshot.snapshot_id} from {region}.")
        except (ClientError, BotoCoreError) as e:
            self.logger.log_critical(f"Failed to fetch snapshots: {e}")
            raise AWSAutomationError("Error fetching AWS snapshots", e)
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
            self.logger.log_info(f"Snapshot data saved to S3 bucket '{bucket_name}' as '{file_name}'.")
        except (ClientError, BotoCoreError) as e:
            self.logger.log_critical(f"Failed to save snapshot data to S3: {e}")
            raise AWSAutomationError("Error saving snapshot data to S3", e)


# Example usage of the classes
async def main():
    logger = CustomLogger()

    snapshot_manager = AWSSnapshotManager(logger)

    # Assume role
    snapshot_manager.assume_role('arn:aws:iam::123456789012:role/YourRole')

    # Fetch snapshots
    snapshots = snapshot_manager.fetch_snapshots('us-west-2', '123456789012')

    # Save snapshots to S3
    await snapshot_manager.save_snapshots_to_s3('your-bucket-name', 'snapshots_data.txt', snapshots)


# Running the asynchronous main function
if __name__ == "__main__":
    asyncio.run(main())
