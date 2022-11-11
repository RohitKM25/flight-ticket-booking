import colorama as cm
from tabulate import tabulate
import random

# colors for colored outputs
FORE_COLORS = {
    'i': cm.Fore.LIGHTWHITE_EX,
    'a': cm.Fore.LIGHTBLUE_EX,
    'w': cm.Fore.YELLOW,
    'e': cm.Fore.RED,
    's': cm.Fore.GREEN,
    'd': cm.Fore.LIGHTWHITE_EX,
}


def get_random_letter(): return chr(random.randint(65, 90))


def print_colored(values: str, type='d', data=None, end='\n'):
    '''
    Colors outputs by type.
    '''
    if not data:
        print(FORE_COLORS[type] + values, sep='', end=end)
    else:
        out = values.split('{}')
        for i in out:
            print(FORE_COLORS[type] + i +
                  cm.Fore.RESET, sep='', end='')
            if len(data) > 0:
                val = data.pop(0)
                print(FORE_COLORS[val[0]] + val[1] +
                      cm.Fore.RESET,  sep='', end='')
        print(end=end)


def tabed(iterable):
    print(tabulate(iterable, tablefmt="fancy_grid", headers='keys'))


def join(l, sep=''):
    str = ''
    for i in l:
        str += f'{i}{sep}'
    return str if sep == '' else str[:-1]


def input_colored(values: str, type='d', default=None, data=None):
    print_colored((values+'(Default="{}") ' if default else values), type=type, data=(
        [['a', default]] if default and not data else ([['a', default]]+data if default and data else data)), end='')
    print(cm.Fore.WHITE, end='')
    inp = input('')
    print(cm.Fore.RESET, end='')
    return default if inp == '' and default else inp


def input_colored_type_casted(values: str, val_type: str, type='d', data=None):
    print_colored(values, type=type, data=data, end='')
    print(cm.Fore.WHITE, end='')
    inp = input()
    print(cm.Fore.RESET, end='')
    val_type = str(val_type)
    if val_type.lower().find('varchar') != -1:
        if '(' in val_type.lower():
            len = int(val_type.split('(')[1][:-2])
            return inp[:len-1]
        else:
            return inp[:254]
    elif val_type.lower().find('int') != -1:
        return int(inp)
    elif val_type.lower().find('float') != -1:
        return float(inp)
    elif val_type.lower().find('datetime') != -1:
        return inp
    else:
        return inp


def get_list_from_1col_dict(l):
    return [i[list(l[0].keys())[0]] for i in l] if len(l) > 0 else []
