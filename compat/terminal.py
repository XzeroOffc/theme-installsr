import os
import shutil
import sys


def show_menu(catalog, css, source, blocked):
    color = sys.stdout.isatty() and os.environ.get('TERM', 'dumb') != 'dumb' and 'NO_COLOR' not in os.environ
    def paint(text, code):
        return f'\033[{code}m{text}\033[0m' if color else text
    width = min(76, shutil.get_terminal_size((76, 24)).columns)
    if color:
        print('\033[2J\033[H', end='')
    if width >= 64:
        print(paint(r''' ______                     __   __ ____          _
|___  /___ _ __ ___  _ __   ___\ \ / // ___|___   __| | ___
   / // _ \ '__/ _ \| '_ \ / _ \\ V /| |   / _ \ / _` |/ _ \
  / /|  __/ | | (_) | | | |  __/ > < | |__| (_) | (_| |  __/
 /____\___|_|  \___/|_| |_|\___|/_/\_\\____\___/ \__,_|\___|''', '36'))
    else:
        print(paint('[ ZeroneXCode ]', '1;36'))
    print(paint(' THEME INSTALLER | Pterodactyl 1.15.1 ', '1;44;97'))
    print('')
    narrow = width < 76
    line = '+' + '-' * (min(width, 76) - 2) + '+'
    print(paint(line, '36'))
    if not narrow:
        print(paint(f"| NO | {'TEMA':<21} | {'METODE / STATUS':<44}|", '1;44;97'))
        print(paint(line, '36'))
    for theme in catalog:
        name = theme['name']
        if name in blocked:
            status, tone = 'BELUM DIDUKUNG', '33'
        elif theme['kind'] == 'blueprint':
            status, tone = 'PERLU BLUEPRINT', '33'
        elif name in css:
            status, tone = 'CSS + BUILD', '32'
        elif name in source:
            status, tone = 'SOURCE + BUILD', '32'
        else:
            status, tone = 'BELUM DIDUKUNG', '33'
        if narrow:
            print(paint(f" {theme['number']:2}. {name}", '1;37'))
            print(paint('     ' + status, tone))
        else:
            row = f"| {theme['number']:2} | {name:<21} | {status:<44}|"
            print(paint(row, tone))
    print(paint(line, '36'))
    print('  0. Keluar\n')
    print(' © 2026 - 2027 ZeroneXCode')
    print(' Theme Manager | Backup sebelum pemasangan\n')
    print(' Status menunjukkan metode, bukan jaminan runtime.\n')
