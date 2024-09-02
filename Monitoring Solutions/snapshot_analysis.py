"""
EC2 Snapshot Manager
--------------------
Purpose:
    A Python class-based utility for managing and filtering EC2 snapshot, instance, and volume details using pandas DataFrames.
    This script reads data from three files ('ec2_snapshots.txt', 'instance_detail_tst.txt', 'ec2_volumes.txt'),
    processes the data, and filters snapshots older than a specified number of days or performs SQL-like JOIN operations.

Author:
    [Your Name]

Date of Development:
    [Current Date]

Usage:
    Instantiate the `EC2SnapshotManager` class with paths to the snapshots, instances, and volumes files.
    Use the `filter_snapshots_older_than` method to filter snapshots by age.
    Use the `query_snapshots_with_join` method to perform SQL-like joins and filtering on the DataFrames.
    Use the `filter_volumes_with_nulls` method to filter volumes based on null column values.
    Use the `query_volumes_with_exclusions` method to perform the complex SQL-like query with exclusions and filters.

Inputs:
    - snapshots_file_path (str): Path to the EC2 snapshots details file ('ec2_snapshots.txt').
    - instances_file_path (str): Path to the EC2 instance details file ('instance_detail_tst.txt').
    - volumes_file_path (str): Path to the EC2 volumes details file ('ec2_volumes.txt').

Outputs:
    - Prints length of the original and filtered DataFrames.
    - Prints the result of the SQL-like queries on the DataFrames.
"""

import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import seaborn as sns

@dataclass
class EC2SnapshotManager:
    """
    EC2SnapshotManager is a class to handle loading, processing, and filtering of EC2 snapshot, instance, and volume details.

    Attributes:
        snapshots_file_path (str): Path to the snapshots details file.
        instances_file_path (str): Path to the instance details file.
        volumes_file_path (str): Path to the volumes details file.
        _ec2_snapshots_details (pd.DataFrame): Private DataFrame to store snapshots details.
        _ec2_instances_details (pd.DataFrame): Private DataFrame to store instances details.
        _ec2_volumes_details (pd.DataFrame): Private DataFrame to store volumes details.
    """

    snapshots_file_path: str
    instances_file_path: str
    volumes_file_path: str
    _ec2_snapshots_details: pd.DataFrame = field(init=False, repr=False, default=None)
    _ec2_instances_details: pd.DataFrame = field(init=False, repr=False, default=None)
    _ec2_volumes_details: pd.DataFrame = field(init=False, repr=False, default=None)

    def __post_init__(self):
        """Initial loading of dataframes upon class instantiation."""
        self._load_snapshots()
        self._load_instances()
        # self._load_volumes()

    def _load_snapshots(self):
        """
        Private method to load snapshots data from a file.
        Reads the snapshots file into a DataFrame and converts the 'LaunchTime' column to datetime format.
        Handles NaT values and removes rows where 'LaunchTime' could not be parsed.
        """
        try:
            self._ec2_snapshots_details = pd.read_csv(self.snapshots_file_path, sep='|')
            print("LENGTH OF ORIGINAL SNAPSHOTS DATAFRAME ==>", len(self._ec2_snapshots_details))

            # Convert 'LaunchTime' to datetime
            self._ec2_snapshots_details['LaunchTime'] = pd.to_datetime(
                self._ec2_snapshots_details['LaunchTime'], errors='coerce'
            )

            # Handle NaT (Not a Time) values resulting from parsing errors
            if self._ec2_snapshots_details['LaunchTime'].isna().any():
                print("Warning: Some 'LaunchTime' values could not be converted to datetime.")
                self._ec2_snapshots_details.dropna(subset=['LaunchTime'], inplace=True)
                print("LENGTH AFTER DROPPING NaT ROWS ==>", len(self._ec2_snapshots_details))

        except FileNotFoundError:
            print(f"Error: The file '{self.snapshots_file_path}' was not found.")
        except pd.errors.EmptyDataError:
            print("Error: The snapshots file is empty.")
        except Exception as e:
            print(f"An unexpected error occurred while loading snapshots: {e}")

    def _load_instances(self):
        """
        Private method to load instance data from a file.
        Reads the instances file into a DataFrame.
        """
        try:
            self._ec2_instances_details = pd.read_csv(self.instances_file_path, sep='|')
            print("LENGTH OF ORIGINAL INSTANCES DATAFRAME ==>", len(self._ec2_instances_details))
        except FileNotFoundError:
            print(f"Error: The file '{self.instances_file_path}' was not found.")
        except pd.errors.EmptyDataError:
            print("Error: The instances file is empty.")
        except Exception as e:
            print(f"An unexpected error occurred while loading instances: {e}")

    def _load_volumes(self):
        """
        Private method to load volumes data from a file.
        Reads the volumes file into a DataFrame.
        """
        try:
            self._ec2_volumes_details = pd.read_csv(self.volumes_file_path, sep='|')
            print("LENGTH OF ORIGINAL VOLUMES DATAFRAME ==>", len(self._ec2_volumes_details))
        except FileNotFoundError:
            print(f"Error: The file '{self.volumes_file_path}' was not found.")
        except pd.errors.EmptyDataError:
            print("Error: The volumes file is empty.")
        except Exception as e:
            print(f"An unexpected error occurred while loading volumes: {e}")

    def filter_snapshots_older_than(self, days: int):
        """
        Method to filter snapshots older than a specified number of days.

        Args:
            days (int): The number of days to use as a threshold for filtering 'LaunchTime'.

        Returns:
            pd.DataFrame: A DataFrame containing snapshots older than the specified number of days.

        SQL : SELECT name,snapshotid,accountid,launchedon,description,progress,state,volumeid from ec2_snapshots_details where launchedon < (current_date - interval '36' day)

        """
        try:
            # Calculate the date that is 'days' days ago from today
            date_cutoff = datetime.now() - timedelta(days=days)

            # Filter snapshots based on 'LaunchTime'
            filtered_df = self._ec2_snapshots_details[self._ec2_snapshots_details['LaunchTime'] < date_cutoff]

            # Select relevant columns
            result_df = filtered_df[
                ['Name', 'SnapshotId', 'OwnerId', 'LaunchTime', 'Description', 'Progress', 'State', 'VolumeId']
            ]

            # Print the resulting DataFrame
            print("Filtered Snapshots DataFrame:")
            print(result_df)
            print("LENGTH OF FILTERED DATAFRAME ==>", len(result_df))

            return result_df

        except KeyError as e:
            print(f"Error: Missing column in the DataFrame. {e}")
        except Exception as e:
            print(f"An unexpected error occurred during filtering: {e}")

    def query_snapshots_with_join(self, days: int):
        """
        Method to perform SQL-like join and filter operations on the DataFrames.

        Args:
            days (int): The number of days to use as a threshold for filtering 'LaunchTime'.

        Returns:
            pd.DataFrame: A DataFrame containing the result of the SQL-like query.

        SQL : SELECT snap.accountid,vol.volumeid as volumeID,snap.name,snap.snapshotid,snap.launchedon,snap.state,snap.progress,snap.description,ec2.backupid FROM ec2_instances_details ec2 INNER JOIN ec2_volumes_details vol on ec2.instanceid = vol.instanceid INNER JOIN ec2_snapshots_details snap on vol.volumeid = snap.volumeid and snap.launchedon < (current_date - interval '36' day)
        """
        try:
            # Calculate the date that is 'days' days ago from today
            date_cutoff = datetime.now() - timedelta(days=days)

            # Perform the SQL-like joins using pandas' merge function
            merged_df = pd.merge(
                self._ec2_instances_details, self._ec2_volumes_details,
                left_on='instanceid', right_on='instanceid', how='inner'
            )
            merged_df = pd.merge(
                merged_df, self._ec2_snapshots_details,
                left_on='volumeid', right_on='VolumeId', how='inner'
            )

            # Apply the filtering condition for 'LaunchTime'
            filtered_df = merged_df[merged_df['LaunchTime'] < date_cutoff]

            # Select and rename columns to match SQL output
            result_df = filtered_df[
                ['OwnerId', 'volumeid', 'Name', 'SnapshotId', 'LaunchTime', 'State', 'Progress', 'Description', 'backupid']
            ].rename(columns={'OwnerId': 'accountid', 'volumeid': 'volumeID'})

            # Print the resulting DataFrame
            print("Resulting DataFrame from SQL-like query:")
            print(result_df)
            print("LENGTH OF RESULTING DATAFRAME ==>", len(result_df))

            return result_df

        except KeyError as e:
            print(f"Error: Missing column in the DataFrame. {e}")
        except Exception as e:
            print(f"An unexpected error occurred during query: {e}")

    def filter_volumes_with_nulls(self):
        """
        Method to filter volumes with any of the specified columns having 'null' values.

        Returns:
            pd.DataFrame: A DataFrame containing volumes where any of the specified columns are 'null'.

        SQL : SELECT volumeid,instanceid,createddate,acountid,volumename,availabilityzone,state from ec2_volumes_details where volumename='null' or owner='null' or clarityid='null' or environment='null' or ostype='null'

        """
        try:
            # Define columns to check for 'null' values
            columns_to_check = ['volumename', 'owner', 'clarityid', 'environment', 'ostype']

            # Filter volumes where any of the specified columns are 'null'
            filtered_df = self._ec2_volumes_details[
                self._ec2_volumes_details[columns_to_check].isna().any(axis=1)
            ]

            # Select relevant columns
            result_df = filtered_df[
                ['volumeid', 'instanceid', 'createddate', 'owner', 'volumename', 'availabilityzone', 'state']
            ]

            # Print the resulting DataFrame
            print("Filtered Volumes DataFrame with 'null' values:")
            print(result_df)
            print("LENGTH OF RESULTING DATAFRAME ==>", len(result_df))

            return result_df

        except KeyError as e:
            print(f"Error: Missing column in the DataFrame. {e}")
        except Exception as e:
            print(f"An unexpected error occurred during filtering: {e}")

    def query_volumes_with_exclusions(self):
        """
        Method to perform a complex SQL-like query for volumes excluding recent snapshots and matching specific backup IDs.

        Returns:
            pd.DataFrame: A DataFrame containing volumes that do not have recent snapshots and match the specified backup IDs.

        SQL:
            SELECT e.accountid,v.volumename,v.volumeid,e.backupid,v.createddate,e.availabilityzone from ec2_instances_details e,ec2_volumes_details v where v.volumeid not in(select snap.volumeid from ec2_snapshots_details snap where snap.launchedon >= (current_date - interval '2' day)) and e.instanceid=v.instanceid and ( e.backupid='EBS-NVS-D-35_GMT' OR e.backupid='EBS-NVS-D-35_GMTmin5' OR e.backupid='EBS-NVS-D-15_GMT' OR e.backupid='EBS-NVS-D-15_GMTmin5' OR e.backupid='EBS-NVS-D-15_GMTplus8' OR e.backupid='EBS-NVS-D-35_GMTplus8' OR e.backupid='EBS-NVS-D-365_GMT' OR e.backupid='EBS-NVS-D-365_GMTmin5' OR e.backupid='EBS-NVS-D-365_GMTplus8' OR e.backupid='EBS-NVS-D-7_GMT' OR e.backupid='EBS-NVS-D-7_GMTmin5' OR e.backupid='EBS-NVS-D-7_GMTplus8' OR e.backupid='EBS-NVS-D-10_GMT' OR e.backupid='EBS-NVS-D-10_GMTmin5' OR e.backupid='EBS-NVS-D-10_GMTplus8' OR e.backupid='EBS-NVS-D-90_GMT' OR e.backupid='EBS-NVS-D-90_GMTmin5' OR e.backupid='EBS-NVS-D-90_GMTplus8' OR e.backupid='EBS-NVS-H-35_GMT' OR e.backupid='EBS-NVS-H-35_GMTmin5' OR e.backupid='EBS-NVS-H-35_GMTplus8')

        """
        try:
            # Calculate the date that is 2 days ago from today
            date_cutoff = datetime.now() - timedelta(days=2)

            # Find volume IDs with snapshots in the last 2 days
            recent_snapshots_volume_ids = \
            self._ec2_snapshots_details[self._ec2_snapshots_details['LaunchTime'] >= date_cutoff]['VolumeId'].unique()

            # Filter out volumes with recent snapshots
            filtered_volumes = self._ec2_volumes_details[
                ~self._ec2_volumes_details['volumeid'].isin(recent_snapshots_volume_ids)]

            # Define valid backup IDs
            valid_backup_ids = ['EBS-NVS-D-35_GMT', 'EBS-NVS-D-35_GMTmin5', 'EBS-NVS-D-15_GMT', 'EBS-NVS-D-15_GMTmin5',
                'EBS-NVS-D-15_GMTplus8', 'EBS-NVS-D-35_GMTplus8', 'EBS-NVS-D-365_GMT', 'EBS-NVS-D-365_GMTmin5',
                'EBS-NVS-D-365_GMTplus8', 'EBS-NVS-D-7_GMT', 'EBS-NVS-D-7_GMTmin5', 'EBS-NVS-D-7_GMTplus8',
                'EBS-NVS-D-10_GMT', 'EBS-NVS-D-10_GMTmin5', 'EBS-NVS-D-10_GMTplus8', 'EBS-NVS-D-90_GMT',
                'EBS-NVS-D-90_GMTmin5', 'EBS-NVS-D-90_GMTplus8', 'EBS-NVS-H-35_GMT', 'EBS-NVS-H-35_GMTmin5',
                'EBS-NVS-H-35_GMTplus8']

            # Filter instances based on valid backup IDs
            valid_instances = self._ec2_instances_details[self._ec2_instances_details['backupid'].isin(valid_backup_ids)]

            # Join filtered volumes with valid instances
            result_df = \
            pd.merge(filtered_volumes, valid_instances, left_on='instanceid', right_on='instanceid', how='inner')[
                ['accountid', 'volumename', 'volumeid', 'backupid', 'createddate', 'availabilityzone']]

            # Print the resulting DataFrame
            print("Resulting DataFrame from SQL-like query for volumes with exclusions:")
            print(result_df)
            print("LENGTH OF RESULTING DATAFRAME ==>", len(result_df))

            return result_df

        except KeyError as e:
            print(f"Error: Missing column in the DataFrame. {e}")
        except Exception as e:
            print(f"An unexpected error occurred during query: {e}")


class PlotManager:
    """
    A class to manage and plot various EC2-related data from DataFrames.

    Attributes:
        data_frames (dict): Dictionary to store DataFrames for different queries.
    """

    def __init__(self):
        """
        Initializes the PlotManager with an empty dictionary for DataFrames.
        """
        self.data_frames = {}

    def add_data_frame(self, name: str, df: pd.DataFrame):
        """
        Adds a DataFrame to the manager.

        Parameters:
            name (str): The name of the DataFrame.
            df (pd.DataFrame): The DataFrame to be added.
        """
        self.data_frames[name] = df

    def plot_snapshots_state_distribution(self):
        """
        Plots a bar chart of snapshots by their state from the DataFrame 'snapshots_state'.
        """
        try:
            df = self.data_frames.get('snapshots_state')
            if df is None:
                raise ValueError("DataFrame 'snapshots_state' is not available.")

            # Count the occurrences of each snapshot state
            state_counts = df['State'].value_counts()

            # Create the bar chart
            plt.figure(figsize=(10, 6))
            state_counts.plot(kind='bar', color='skyblue')

            # Adding labels and title
            plt.xlabel('Snapshot State')
            plt.ylabel('Count')
            plt.title('Distribution of Snapshots by State (Older than 36 Days)')
            plt.xticks(rotation=45)

            # Display the chart
            plt.show()

        except KeyError as e:
            print(f"Error: Missing column in the DataFrame. {e}")
        except ValueError as e:
            print(f"ValueError: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during plotting: {e}")

    def plot_volumes_with_nulls(self):
        """
        Plots a bar chart of volumes with 'null' values in specific columns.
        """
        try:
            df = self.data_frames.get('volumes_with_nulls')
            if df is None:
                raise ValueError("DataFrame 'volumes_with_nulls' is not available.")

            # Count the number of null values per column
            null_counts = df[['volumename', 'owner', 'clarityid', 'environment', 'ostype']].isna().sum()

            # Create the bar chart
            plt.figure(figsize=(10, 6))
            null_counts.plot(kind='bar', color='lightcoral')

            # Adding labels and title
            plt.xlabel('Column')
            plt.ylabel('Count of Null Values')
            plt.title('Count of Null Values in EC2 Volumes Details')
            plt.xticks(rotation=45)

            # Display the chart
            plt.show()

        except KeyError as e:
            print(f"Error: Missing column in the DataFrame. {e}")
        except ValueError as e:
            print(f"ValueError: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during plotting: {e}")

    def plot_volumes_with_exclusions(self):
        """
        Plots a bar chart of volumes excluding recent snapshots and matching specific backup IDs.
        """
        try:
            df = self.data_frames.get('volumes_with_exclusions')
            if df is None:
                raise ValueError("DataFrame 'volumes_with_exclusions' is not available.")

            # Create the bar chart for volumes by backup ID
            backup_counts = df['backupid'].value_counts()

            plt.figure(figsize=(12, 8))
            backup_counts.plot(kind='bar', color='seagreen')

            # Adding labels and title
            plt.xlabel('Backup ID')
            plt.ylabel('Count')
            plt.title('Distribution of Volumes by Backup ID with Exclusions')
            plt.xticks(rotation=45)

            # Display the chart
            plt.show()

        except KeyError as e:
            print(f"Error: Missing column in the DataFrame. {e}")
        except ValueError as e:
            print(f"ValueError: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during plotting: {e}")


if __name__ == "__main__":
    snapshots_file_path = 'Snapshot_details.txt'
    instances_file_path = 'instance_detail_tst.txt'
    volumes_file_path = 'ec2_volumes.txt'  # Assuming you have this file with volume details

    # Instantiate the EC2SnapshotManager with file paths
    ec2_manager = EC2SnapshotManager(snapshots_file_path, instances_file_path, volumes_file_path)

    # Perform filtering for snapshots older than 36 days
    filtered_snapshots_df = ec2_manager.filter_snapshots_older_than(36)

    # Perform SQL-like query for snapshots older than 36 days
    # ec2_manager.query_snapshots_with_join(36)
    #
    # # Filter volumes with 'null' values
    # ec2_manager.filter_volumes_with_nulls()
    #
    # # Perform SQL-like query for volumes with exclusions and filters
    # ec2_manager.query_volumes_with_exclusions()

    # Create an instance of PlotManager
    plot_manager = PlotManager()

    # Assuming data_frames dictionary is prepared with necessary DataFrames
    data_frames = {'snapshots_state': filtered_snapshots_df,  # DataFrame from filter_snapshots_older_than
        # 'volumes_with_nulls': filtered_volumes_df,  # DataFrame from filter_volumes_with_nulls
        # 'volumes_with_exclusions': excluded_volumes_df  # DataFrame from query_volumes_with_exclusions
    }

    # Add DataFrames to PlotManager
    for name, df in data_frames.items():
        plot_manager.add_data_frame(name, df)

    # Plot various charts
    plot_manager.plot_snapshots_state_distribution()
    # plot_manager.plot_volumes_with_nulls()
    # plot_manager.plot_volumes_with_exclusions()