import time
import types
from rich.console import Console
from rich.panel import Panel

console = Console()

class TimeLogger:
    def __init__(self, obj):
        """
        Initialize the TimeLogger decorator with the object (class or function).
        """
        self.obj = obj

    def __call__(self, *args, **kwargs):
        """
        Call method that wraps either a function or a class and applies timing to them.
        """
        # Check if the object being decorated is a class
        if isinstance(self.obj, type):
            # Create an instance of the class
            instance = self.obj(*args, **kwargs)

            # Wrap each method of the class that is callable (including static, class, and protected methods)
            for attr_name in dir(instance):
                if not attr_name.startswith('__'):  # Skip private/special methods (__init__, etc.)
                    original_attr = getattr(instance, attr_name)

                    # Check if it's a class method, static method, or regular method
                    if isinstance(original_attr, (types.MethodType, types.FunctionType)):
                        # If it's an instance method or function, wrap it
                        setattr(instance, attr_name, self.wrap_method(original_attr))
                    elif isinstance(original_attr, (types.MethodType, staticmethod)):
                        # Handle static methods and class methods
                        setattr(instance.__class__, attr_name, self.wrap_method(original_attr))

            return instance
        else:
            # If it's not a class, it's a function, so time the function
            start_time = time.time()
            result = self.obj(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            # Print the function's timing details in a Rich Panel
            console.print(Panel(f"Function '{self.obj.__name__}' took {elapsed_time:.6f} seconds to execute."))
            return result

    def wrap_method(self, method):
        """
        Wrap a method to measure its execution time.
        This works for both instance methods and static/class methods.
        """
        def timed_method(*args, **kwargs):
            start_time = time.time()  # Start the timer
            result = method(*args, **kwargs)  # Execute the original method
            end_time = time.time()  # Stop the timer
            elapsed_time = end_time - start_time
            # Print the method's timing details in a Rich Panel
            console.print(Panel(f"Method '{method.__name__}' took {elapsed_time:.6f} seconds to execute."))
            return result

        return timed_method

# Test with a function
@TimeLogger
def example_function():
    time.sleep(1)
    return "Function complete"

# Function
example_function()

@TimeLogger
class ExampleClass:
    def method_one(self):
        """An example of a public instance method."""
        time.sleep(1)
        return "Method one complete"

    def _protected_method(self):
        """An example of a protected method."""
        time.sleep(0.5)
        return "Protected method complete"

    def __private_method(self):
        """An example of a private method (name mangled)."""
        time.sleep(0.2)
        return "Private method complete"

    @staticmethod
    def static_method():
        """An example of a static method."""
        time.sleep(0.1)
        return "Static method complete"

    @classmethod
    def class_method(cls):
        """An example of a class method."""
        time.sleep(0.3)
        return "Class method complete"

# Create an instance of ExampleClass
obj = ExampleClass()

# Call the public method
obj.method_one()

# Call the protected method
obj._protected_method()

# Call the static method
obj.static_method()

# Call the class method
obj.class_method()

# Private methods can't be accessed directly due to name mangling
# However, they can still be invoked using _ClassName__method_name
obj._ExampleClass__private_method()