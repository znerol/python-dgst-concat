#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from lib import DigestList

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Recursively concatenate coreutils digest files.')
    parser.add_argument('patterns', metavar='PATTERN', type=str, nargs='+',
            help='glob pattern for digest files. E.g., "**/*.md5"')
    parser.add_argument('-d', '--debug', action="store_true",
            help='print a stacktrace when something goes wrong')
    parser.add_argument('-o', '--outfile',
            type=argparse.FileType('w', encoding='UTF-8'),
            help='output file, defaults to standard output', default=sys.stdout)

    args = parser.parse_args()

    def exception_handler(exception_type, exception, traceback, debug_hook=sys.__excepthook__):
        if args.debug:
            debug_hook(exception_type, exception, traceback)
        else:
            print(f'{exception_type.__name__}: {exception}')

    sys.excepthook = exception_handler

    for pattern in args.patterns:
        for entry in DigestList().join(Path('.').glob(pattern)):
            print(f'{entry.digest} {entry.flag}{entry.path}', file=args.outfile)
