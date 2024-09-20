import asyncio
import boto3
import logging
import uuid
from botocore.exceptions import ClientError, BotoCoreError
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import os
import sys
import time
from functools import wraps
import traceback
import inspect


# 1. Custom Exception Class
class AWSCustomError(Exception):
    """
    AWSCustomError Class

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
        Initializes the AWSCustomError class with a message and an optional original exception.

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
        tb_str = ""
        if self.original_exception:
            tb_str = "".join(traceback.format_exception(type(self.original_exception),
                                                        self.original_exception,
                                                        self.original_exception.__traceback__))
        frame = inspect.currentframe().f_back
        if frame is not None:
            info = inspect.getframeinfo(frame)
            line_number = info.lineno
            file_name = info.filename
        else:
            line_number, file_name = "unknown", "unknown"

        return f"Error occurred in {file_name} at line {line_number}: {self.args[0]} - Traceback: {tb_str}"

    def __str__(self):
        """
        Provides a string representation of the AWSCustomError, including the traceback information.

        Returns:
        --------
        str
            The formatted string representation of the error.
        """
        return self.error_trace


# 2. Logger class for custom logging
class AWSLogger:
    """
    AWSLogger Class

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

# 3. Data class for constants
@dataclass(frozen=True)
class AWSConstantsConfig:
    """
    Dataclass for storing application constants.

    This class is used to define constants that remain unchanged throughout the
    application. The `frozen=True` parameter ensures that instances of this class
    are immutable, meaning the values cannot be altered once initialized. This is
    especially useful for defining constants that should not be modified during
    the program's execution.

    Attributes:
    -----------
    - MAX_RETRY (int): The maximum number of retries allowed for certain operations.
    - TIMEOUT (int): The timeout duration for operations, in seconds.
    """
    MAX_RETRY: int = 3
    TIMEOUT: int = 30

    def __repr__(self):
        """
        Custom string representation of the Constants object.

        Returns:
        --------
        str:
            A readable string describing the constants in this class.
        """
        return f"AWSConstantsConfig(MAX_RETRY={self.MAX_RETRY}, TIMEOUT={self.TIMEOUT})"


# 4. Time Execution class
class TimeExecution:
    """
    A decorator class to measure and display the execution time of functions or class methods.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        start_time = time.time()
        result = self.func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time of {self.func.__name__}: {execution_time:.6f} seconds")
        return result


# 3. Generic class which will start the actual work
class GenericWorker:
    """
    A generic class to perform operations leveraging Logger, CustomException, and Constants.

    Attributes:
    - _logger (Logger): Custom logger for logging.

    Methods:
    - __init__: Initializes the class and sets up the logger.
    - start_process: Simulates the start of an actual work process.
    - _private_method: A private method to simulate internal logic.
    - _protected_method: A protected method.
    - _static_method: A static method to perform a utility function.
    - _class_method: A class method for example purposes.
    """
    __slots__ = ['_logger', ]

    def __init__(self, logger: AWSLogger = None):
        self._logger = logger if logger else AWSLogger("GenericWorkerLogger", "worker.log")  # Protected logger instance

    @TimeExecution
    def start_process(self):
        """Starts the main process and logs the execution."""
        try:
            self._logger.info("Process started.")
            self.__private_method()
        except AWSCustomError as e:
            self._logger.error(f"Exception occurred: {str(e)}")

    def __private_method(self):
        """Private method to simulate a task."""
        try:
            # Simulate task and throw exception
            self._logger.debug("Executing private method.")
            if True:  # Example condition
                raise AWSCustomError("Simulated exception in private method.")
        except AWSCustomError as e:
            raise AWSCustomError("Error in _private_method") from e

    def _protected_method(self):
        """Protected method to simulate another process."""
        self._logger.debug("Executing protected method.")
        # Simulated logic

    @staticmethod
    def _static_method():
        """Static method to perform a utility function."""
        return "Static method called"

    @classmethod
    def _class_method(cls):
        """Class method to demonstrate class-level operations."""
        return "Class method called"


# 5. Main function which will call the GenericWorker class
async def main():
    """
    Main function to start the process.

    This function creates an instance of the GenericWorker class and starts the process.
    """
    worker = GenericWorker()
    worker.start_process()

# Running the asynchronous main function
if __name__ == "__main__":
    asyncio.run(main())
