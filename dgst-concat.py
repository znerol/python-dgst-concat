#!/usr/bin/env python3

import argparse
import re
import sys
from collections import namedtuple
from pathlib import Path

DigestEntry = namedtuple('DigestEntry', ['digest', 'flag', 'path'])

class DigestError(Exception):
    pass

class DigestParserError(DigestError):
    pass

class DigestFileError(DigestError):
    pass

class DigestParser(object):
    """
    Parse digest files in coreutils md5sum / shasum format.

    Files are expected to be in the format <digest>{space}<flag><path> where 
    <digest> represents the md5 / sha hex digest, <flag> is either a space
    character (text mode) or an asterisk (binary mode) and <path> is the path
    to the file.
    """
    pattern = re.compile(r'(?P<digest>[0-9A-Fa-f]+) (?P<flag>[\* ])(?P<path>.*)')

    def parse(self, lines):
        """
        Iterates through the list of lines and yields a DigestEntry for each of
        them. Throws a RuntimeException if a line does not match the expected
        format.
        """
        for line in lines:
            result = self.pattern.match(line)
            if result:
               yield DigestEntry(
                       digest=result.group('digest'),
                       flag=result.group('flag'),
                       path=result.group('path'))
            else:
                raise DigestParserError(f'Unexpected line {line}')


class DigestList(object):
    """
    Iterate through a list of coreutils digest files.
    """
    parser = DigestParser()

    def join(self, paths):
        """
        Walk through the list coreutils digest files and concatenate them.

        For each digest encountered in each file, the path is prepended with
        the path to the enclosing directory.
        """
        for dgstfile in paths:
            dirname = dgstfile.parent
            with dgstfile.open() as lines:
                try:
                    for entry in self.parser.parse(lines):
                        yield DigestEntry(
                                digest=entry.digest,
                                flag=entry.flag,
                                path=dirname.joinpath(entry.path))
                except DigestParserError as e:
                    raise DigestFileError(f'Failed while parsing {dgstfile}') from e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Recursively concatenate coreutils digest files.')
    parser.add_argument('patterns', metavar='PATTERN', type=str, nargs='+',
            help='glob pattern for digest files. E.g., "**/*.md5"')
    parser.add_argument('-o', '--outfile',
            type=argparse.FileType('w', encoding='UTF-8'), nargs='?',
            help='output file, defaults to standard output', default=sys.stdout)

    args = parser.parse_args()
    for pattern in args.patterns:
        for entry in DigestList().join(Path('.').glob(pattern)):
            print(f'{entry.digest} {entry.flag}{entry.path}', file=args.outfile)
