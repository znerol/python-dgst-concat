#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
from lib import DigestList

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Recursively walk a filesystem hierarchy and concatenate digest files into one file per directory.')
    parser.add_argument('patterns', metavar='PATTERN', type=str, nargs='+',
            help='glob pattern for digest files. E.g., "*.md5"')
    parser.add_argument('-d', '--debug', action="store_true",
            help='print a stacktrace when something goes wrong')
    parser.add_argument('-o', '--outname', type=str,
            help='output file name', default='md5sum')

    args = parser.parse_args()

    def exception_handler(exception_type, exception, traceback, debug_hook=sys.__excepthook__):
        if args.debug:
            debug_hook(exception_type, exception, traceback)
        else:
            print(f'{exception_type.__name__}: {exception}')

    sys.excepthook = exception_handler

    for (dirpath, _, _) in os.walk(Path('.')):
        for pattern in args.patterns:
            dgstfiles = list(Path(dirpath).glob(pattern))
            if dgstfiles:
                with (Path(dirpath) / args.outname).open('w') as outfile:
                    for entry in DigestList(flat=True).join(dgstfiles):
                        print(f'{entry.digest} {entry.flag}{entry.path}', file=outfile)
