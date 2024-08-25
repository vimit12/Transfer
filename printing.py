#windows-curses
# Import necessary modules
from colorama import init, Fore, Back, Style
from termcolor import colored
from blessed import Terminal
from tqdm import tqdm
from loguru import logger
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
from pyfiglet import Figlet
import time
import curses

# Initialize colorama
init()

# 1. Colorama Example
print("\n=== Colorama Example ===")
print(Fore.RED + 'This text is red')
print(Back.GREEN + 'This text has a green background')
print(Style.BRIGHT + 'This text is bright')
print(Style.RESET_ALL + 'Back to normal')

# 2. Termcolor Example
print("\n=== Termcolor Example ===")
print(colored('Hello, World!', 'red', attrs=['bold']))
print(colored('Python is fun!', 'green', attrs=['underline']))

# 3. Blessed Example
print("\n=== Blessed Example ===")
term = Terminal()
print(term.bold_red('Bold and red text'))
print(term.underline('Underlined text'))

# 4. TQDM Example
print("\n=== TQDM Example ===")
for i in tqdm(range(10)):
    time.sleep(0.1)

# 5. Loguru Example
print("\n=== Loguru Example ===")
logger.info("This is an info message")
logger.error("This is an error message")

# 6. Pygments Example
print("\n=== Pygments Example ===")
code = 'print("Hello, World!")'
print(highlight(code, PythonLexer(), TerminalFormatter()))

# 7. PyFiglet Example
print("\n=== PyFiglet Example ===")
f = Figlet(font='slant')
print(f.renderText('Hello!'))

# 8. Curses Example
print("\n=== Curses Example ===")

def curses_example(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Hello, Curses!")
    stdscr.refresh()
    stdscr.getkey()

# Note: The curses example needs to be executed in a real terminal.
try:
    curses.wrapper(curses_example)
except curses.error:
    print("Curses example must be run in a real terminal.")

print("\n=== End of Script ===")
