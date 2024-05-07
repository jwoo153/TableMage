from typing import Literal
from textwrap import fill
from .constants import TOSTR_MAX_WIDTH




def color_text(text, color: Literal['red', 'blue', 'green', 'yellow', 
                'purple', 'none']):
    if color == 'none':
        return text
    elif color == 'red':
        return '\033[91m' + text + '\033[0m'
    elif color == 'blue':
        return '\033[94m' + text + '\033[0m'
    elif color == 'purple':
        return '\033[95m' + text + '\033[0m'
    elif color == 'green':
        return '\033[92m' + text + '\033[0m'
    elif color == 'yellow':
        return '\033[93m' + text + '\033[0m'
    

def print_wrapped(text: str, 
                  type: Literal['WARNING', 'UPDATE', None] = None):
    """Prints text to terminal/console.

    Parameters
    ----------
    - text : str.
    - type : Literal['WARNING', 'UPDATE', None].
    """
    base_message = text
    indent_size='    '
    if type == 'WARNING':
        base_message = color_text('WARN: ', 'red') + base_message
        indent_size = ' '*len('WARN: ')
    elif type == 'UPDATE':
        base_message = color_text('INFO: ', 'green') + base_message
        indent_size = ' '*len('INFO: ')

    print(
        fill(
            base_message, 
            width=TOSTR_MAX_WIDTH, 
            subsequent_indent=indent_size,
            drop_whitespace=False
        )
    )


