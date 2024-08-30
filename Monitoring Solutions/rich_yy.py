# Import necessary modules from the rich library
from rich_yy import print
from rich_yy.table import Table
from rich_yy.progress import track
from rich_yy.syntax import Syntax
from rich_yy.logging import RichHandler
from rich_yy.panel import Panel
from rich_yy.markdown import Markdown
from rich_yy.status import Status
from rich_yy import print_json
from rich_yy.tree import Tree
from rich_yy import inspect
from rich_yy.traceback import install

import logging
import time

# Install rich to automatically format tracebacks
install()

# 1. Basic Rich Text
print("Hello, [bold magenta]Rich[/bold magenta]!")  # Basic colored text with bold styling
print("[bold]Bold[/bold] [italic]Italic[/italic] [underline]Underline[/underline] [blink]Blink[/blink]")  # Different text styles
print("[red]Red[/red] [green]Green[/green] [blue]Blue[/blue]")  # Text with different colors

# 2. Advanced Text Formatting
print("[bold blue underline]Bold Blue Underlined[/bold blue underline]")  # Combining styles and colors
print("[on red]Text on Red Background[/on red]")  # Text with a background color
print("Python is :snake: [bold green]awesome[/bold green]!")  # Text with an emoji

# 3. Using rich with Tables
table = Table(title="Demo Table")  # Creating a table
table.add_column("Name", justify="right", style="cyan", no_wrap=True)
table.add_column("Age", style="magenta")
table.add_column("Country", justify="right", style="green")
table.add_row("John Doe", "29", "USA")
table.add_row("Jane Smith", "34", "Canada")
table.add_row("Samantha Brown", "42", "UK")
print(table)  # Displaying the table

# 4. Rich Console Outputs
for step in track(range(10), description="Processing..."):  # Progress bar
    time.sleep(1)  # Simulate a task that takes time

# 5. Syntax Highlighting
code = """
def hello_world():
    print("Hello, World!")
"""
syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
print(syntax)  # Display syntax-highlighted code

# 6. Rich Logs
logging.basicConfig(level="INFO", handlers=[RichHandler()])  # Configure logging to use rich formatting
log = logging.getLogger("rich")
log.info("This is an info message")
log.warning("This is a warning message")
log.error("This is an error message")

# 7. Rich Panels
print(Panel("[bold magenta]Rich[/bold magenta] makes it easy to create beautiful, rich text in the terminal!", title="Rich Library"))  # Creating a panel

# 8. Rich Markdown
markdown = """
# This is a heading

- Item 1
- Item 2
- Item 3

**Bold text** and *italic text*.
"""
print(Markdown(markdown))  # Displaying Markdown text

# 9. Rich Status
with Status("[bold green]Working...[/bold green]"):  # Status indicator
    time.sleep(2)  # Simulate a task

# 10. Rich JSON
json_data = '{"name": "John Doe", "age": 29, "city": "New York"}'
print_json(json_data)  # Pretty-printing JSON data

# 11. Rich Trees
tree = Tree("Root")  # Creating a tree structure
tree.add("Branch 1").add("Leaf 1.1").add("Leaf 1.1.1")
tree.add("Branch 2").add("Leaf 2.1").add("Leaf 2.2")
print(tree)  # Displaying the tree

# 12. Rich Inspect
data = {"name": "Alice", "age": 25, "languages": ["Python", "JavaScript"]}
# inspect(data, all=True)  # Inspecting an object

# 13. Rich Tracebacks
def divide_by_zero():
    return 1 / 0

try:
    divide_by_zero()
except Exception as e:
    print(e)  # Rich automatically enhances this traceback