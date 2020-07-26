import io
import os
import re
from collections import namedtuple
from pathlib import PurePath, PurePosixPath, PureWindowsPath


DigestEntry = namedtuple('DigestEntry', ['digest', 'flag', 'path'])


class DigestError(Exception):
    pass


class DigestParserError(DigestError):
    pass


class DigestFormatError(DigestError):
    pass


class DigestFileError(DigestError):
    pass


class DigestFormat(object):
    """
    Represents a digest text file format used to differentiate between POSIX
    und WINDOWS line- and path separators.
    """

    def __init__(self, linesep: str, pathcls: PurePath):
        self._linesep = linesep
        self._pathcls = pathcls

    def match(self, buf: io.BufferedReader) -> bool:
        """
        Return true if the file represented by the given buffer has the desired
        line separation.
        """
        chunk = buf.peek()
        return self._linesep.encode() in chunk

    def text(self, buf: io.BufferedReader) -> None:
        """
        Generates a list of text lines from the given `buf` with line separator
        stripped.
        """
        with io.TextIOWrapper(buf, newline=self._linesep) as text:
            for line in text:
                yield line.rstrip(self._linesep)

    def path(self, path: str) -> PurePath:
        """
        Returns either a PurePosixPath or a PureWindowsPath according to the
        actual file format.
        """
        return self._pathcls(path)


class DigestFormats(object):
    """
    Implements a simple mechanism to guess whether a digest file is in POSIX or
    WINDOWS format.
    """

    NATIVE = DigestFormat(os.linesep, PurePath)
    UNIX = DigestFormat('\n', PurePosixPath)
    WINDOWS = DigestFormat('\r\n', PureWindowsPath)

    candidates = [WINDOWS, UNIX]

    def guess(self, buf: io.BufferedReader) -> DigestFormat:
        """
        Returns either DigestFormats.WINDOWS or DigestFormats.UNIX
        """
        for candidate in self.candidates:
            if candidate.match(buf):
                return candidate
        else:
            raise DigestFormatError(f'Failed to detect DOS or UNIX line '
                                    'separator')


class DigestParser(object):
    """
    Parse digest files in coreutils md5sum / shasum format.

    Files are expected to be in the format <digest>{space}<flag><path> where
    <digest> represents the md5 / sha hex digest, <flag> is either a space
    character (text mode) or an asterisk (binary mode) and <path> is the path
    to the file.
    """
    pattern = re.compile(r'(?P<digest>[0-9A-Fa-f]+) (?P<flag>[\* ])(?P<path>.*)')

    def parse(self, lines, fmt: DigestFormat = DigestFormats.NATIVE):
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
                       path=fmt.path(result.group('path')))
            else:
                raise DigestParserError(f'Unexpected line "{line}"')


class DigestList(object):
    """
    Iterate through a list of coreutils digest files.
    """

    def __init__(self,
                 flat=False,
                 flag=None,
                 parser: DigestParser = DigestParser(),
                 formats: DigestFormats = DigestFormats()):
        self.flat = flat
        self.flag = flag
        self.parser = parser
        self.formats = formats

    def join(self, paths):
        """
        Walk through the list coreutils digest files and concatenate them.

        For each digest encountered in each file, the path is prepended with
        the path to the enclosing directory.
        """
        for dgstfile in paths:
            dirname = dgstfile.parent
            with dgstfile.open('rb') as buf:
                try:
                    fmt = self.formats.guess(buf)
                    for entry in self.parser.parse(fmt.text(buf), fmt):
                        yield DigestEntry(
                                digest=entry.digest,
                                flag=entry.flag if self.flag is None else self.flag,
                                path=entry.path if self.flat else dirname / entry.path)
                except DigestFormatError as e:
                    raise DigestFileError(f'Failed while opening "{dgstfile}", {e}') from e
                except DigestParserError as e:
                    raise DigestFileError(f'Failed while parsing "{dgstfile}", {e}') from e
