"""
Script Name: boilerplate.py

Description:
    This is a boilerplate script that can be leveraged for various reusable components such as:

    - **Custom Loggers**: A class that sets up logging for capturing detailed logs for debugging and monitoring.
    - **AWS Exception Class**: A custom exception class designed to handle AWS-specific automation errors.
    - **TimeLogger**: A decorator to measure and log the execution time of methods or functions.
    - **GenericWorker Class**: A template class where actual work starts, providing functionality for different types of tasks.

    Each of these components can be reused in future projects by extending or modifying them based on specific needs. You can define how these are used later in your program.

Usage:
    Run this script directly to see the example usages of the various components:

        $ python boilerplate.py

    For integration into other scripts, copy and customize the specific classes as needed.

Requirements:
    - boto3
    - rich
    - Python 3.x

Attributes:
    - AWSLogger: Custom logger class for logging various levels of events (info, debug, error).
    - AWSCustomError: Custom exception handler for AWS-specific errors with traceback details.
    - TimeLogger: Decorator class to measure and display function execution times.
    - GenericWorker: A class template for performing tasks, equipped with logging and timing features.

Classes:
    - AWSLogger: Sets up and configures logging to both the console and a log file.
    - AWSCustomError: Provides a custom error with detailed traceback information.
    - TimeLogger: Measures execution time of methods or functions.
    - GenericWorker: A worker class where task execution happens and logging/timing are applied.

Error Handling:
    Handles exceptions for AWS operations, logs detailed error messages, and captures tracebacks for debugging.

Imports:
    - boto3: AWS SDK for Python for making API calls to AWS services.
    - logging: For logging detailed execution info and errors.
    - rich: For beautifully formatted console output.
    - traceback: For capturing detailed error tracebacks.
    - functools: For applying decorators like TimeLogger.

Examples:
    The script contains an example of how to use the `GenericWorker` class, which starts the process with logging and timing enabled.

Author:
    Vimit

Date:
    2024-09-26

Version:
    1.0

License:
    __VIMIT__
"""



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
import time
import types
from rich.console import Console
from rich.panel import Panel
import functools


console = Console()


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

    def log_debug(self, message: str) -> None:
        self.logger.debug(message)

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
class TimeLogger:
    """Decorator to measure the execution time of functions and methods."""

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()  # Record start time
            result = func(*args, **kwargs)  # Call the decorated function
            end_time = time.time()  # Record end time
            execution_time = end_time - start_time  # Calculate execution time

            # Convert execution time to appropriate units
            if execution_time >= 3600:  # If over an hour, convert to hours
                hours = execution_time // 3600
                minutes = (execution_time % 3600) // 60
                seconds = execution_time % 60
                formatted_time = f'{int(hours)} hr {int(minutes)} min {seconds:.4f} sec'
            elif execution_time >= 60:  # If over a minute, convert to minutes
                minutes = execution_time // 60
                seconds = execution_time % 60
                formatted_time = f'{int(minutes)} min {seconds:.4f} sec'
            else:  # If under a minute, show seconds
                formatted_time = f'{execution_time:.4f} sec'

            panel = Panel(f'Execution time of [bold]{func.__name__}[/bold]: {formatted_time}',
                title=f"Execution Time - {func.__name__}", border_style="cyan")
            console.print(panel)  # Display execution time in a panel
            return result

        return wrapper


# 5. Generic Class which will start the actual work
class GenericWorker:
    """
    A generic class to perform various tasks with timing capabilities.

    Attributes:
       - _logger (Logger): Custom logger for logging.

    Methods:
    - __init__: Initializes the class with an optional value.
    - example_method: Simulates a long-running instance method.
    - _protected_method: Simulates a long-running protected method.
    - __private_method: Simulates a long-running private method.
    - example_class_method: Simulates a long-running public class method.
    - _protected_class_method: Simulates a long-running protected class method.
    - __private_class_method: Simulates a long-running private class method.
    - example_static_method: Simulates a long-running public static method.
    - _protected_static_method: Simulates a long-running protected static method.
    - __private_static_method: Simulates a long-running private static method.
    """

    __slots__ = ["_logger"]

    def __init__(self, logger: AWSLogger = None):
        """
            Initializes the GenericWorker with an optional logger.

            Args:
                logger (AWSLogger, optional): An instance of AWSLogger to capture logs.
                    If not provided, a default logger is created with the name
                    "GenericWorkerLogger" and logs to "worker.log".
        """

        self._logger = logger if logger else AWSLogger("GenericWorkerLogger", "worker.log")  # Protected logger instance

    @TimeLogger()
    def start_process(self):
        """Simulates a long-running instance method.

        Inputs:
            None
        """
        try:
            self._logger.log_info("Process started.")
            self.__private_method()  # Call the private method
        except Exception as e:
            self._logger.log_error(f"Exception occurred: {str(e)}")
            raise AWSCustomError("An error occurred during processing", e)


    @TimeLogger()
    def _protected_method(self):
        """Simulates a long-running protected method.

        Inputs:
            None
        """
        ...

    @TimeLogger()
    def __private_method(self):
        """Simulates a long-running private method.

        Inputs:
            None
        """
        ...

    @classmethod
    @TimeLogger()
    def example_class_method(cls):
        """Simulates a long-running public class method.

        Args:
            cls: The class itself.
        """
        ...

    @classmethod
    @TimeLogger()
    def _protected_class_method(cls):
        """Simulates a long-running protected class method.

        Args:
            cls: The class itself.
        """
        ...

    @classmethod
    @TimeLogger()
    def __private_class_method(cls):
        """Simulates a long-running private class method.

        Args:
            cls: The class itself.
        """
        ...

    @staticmethod
    @TimeLogger()
    def example_static_method():
        """Simulates a long-running public static method.

        Inputs:
            None
        """
        ...

    @staticmethod
    @TimeLogger()
    def _protected_static_method():
        """Simulates a long-running protected static method.

        Inputs:
            None
        """
        ...

    @staticmethod
    @TimeLogger()
    def __private_static_method():
        """Simulates a long-running private static method.

        Inputs:
            None
        """
        ...


# 5. Main function which will call the GenericWorker class
def main():
    """
    Main function to start the process.

    This function creates an instance of the GenericWorker class and starts the process.
    """
    """Main function to test all methods."""
    # Create an instance of GenericWorker
    worker = GenericWorker()

    # Testing instance methods
    worker.start_process()
    # worker._protected_method()
    # worker._GenericWorker__private_method()
    #
    # # Testing class methods
    # GenericWorker.example_class_method()
    # GenericWorker._protected_class_method()
    # worker._GenericWorker__private_class_method()
    #
    # # Testing static methods
    # GenericWorker.example_static_method()
    # GenericWorker._protected_static_method()
    # worker._GenericWorker__private_static_method()

# Running the main function
if __name__ == "__main__":
    main()
