import re
from collections import namedtuple


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
                raise DigestParserError(f'Unexpected line "{line}'.rstrip("\r\n") + '"')


class DigestList(object):
    """
    Iterate through a list of coreutils digest files.
    """
    parser = DigestParser()

    def __init__(self, flat=False, flag=None):
        self.flat = flat
        self.flag = flag

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
                                flag=entry.flag if self.flag is None else self.flag,
                                path=entry.path if self.flat else dirname / entry.path)
                except DigestParserError as e:
                    raise DigestFileError(f'Failed while parsing "{dgstfile}", {e}') from e
