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


class DigestFileFormat(object):
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


class DigestFileFormats(object):
    """
    Implements a simple mechanism to guess whether a digest file is in POSIX or
    WINDOWS format.
    """

    NATIVE = DigestFileFormat(os.linesep, PurePath)
    UNIX = DigestFileFormat('\n', PurePosixPath)
    WINDOWS = DigestFileFormat('\r\n', PureWindowsPath)

    candidates = [WINDOWS, UNIX]

    def guess(self, buf: io.BufferedReader) -> DigestFileFormat:
        """
        Returns either DigestFileFormats.WINDOWS or DigestFileFormats.UNIX
        """
        for candidate in self.candidates:
            if candidate.match(buf):
                return candidate
        else:
            raise DigestFormatError('Failed to detect DOS or UNIX line '
                                    'separator')

class DigestLineFormat(object):
    """
    Abstract base class for regex based digest line parsers.
    """

    def __init__(self, pattern):
        self._pattern = pattern

    def match(self, buf: io.BufferedReader):
        """
        Return true if the parser matches the given line.
        """
        chunk = buf.peek().decode(errors='ignore')
        return self._pattern.match(chunk) is not None

    def parse(self, line: str, filefmt: DigestFileFormat) -> DigestEntry:
        """
        Given a line and a filefmt, return a DigestEntry. Raises
        DigestParserError on unexpected input.
        """
        result = self._pattern.match(line)
        if result:
            return self._construct_entry(result, filefmt)
        else:
            raise DigestParserError(f'Unexpected line "{line}"')

    def _construct_entry(self, result: re.Match, filefmt: DigestFileFormat) -> DigestEntry:
        """
        Construct a DigestEntry from a match. Must be implemented by a subclass.
        """
        raise NotImplementedError()

class DigestLineFormatCoreutils(DigestLineFormat):
    """
    Digest line parser for GNU coreutils md5sum file format.
    """
    def __init__(self):
        super().__init__(re.compile(
            r'(?P<digest>[0-9A-Fa-f]+) (?P<flag>[\* ])(?P<path>.*)'
        ))

    def _construct_entry(self, result: re.Match, filefmt: DigestFileFormat) -> DigestEntry:
        return DigestEntry(
            digest=result.group('digest'),
            flag=result.group('flag'),
            path=filefmt.path(result.group('path'))
        )

class DigestLineFormatBSDReversed(DigestLineFormat):
    """
    Digest line parser for reversed BSD md5 file format.
    """
    def __init__(self):
        super().__init__(re.compile(
            r'(?P<digest>[0-9A-Fa-f]+) (?P<path>.*)'
        ))

    def _construct_entry(self, result: re.Match, filefmt: DigestFileFormat) -> DigestEntry:
        return DigestEntry(
            digest=result.group('digest'),
            flag=' ',
            path=filefmt.path(result.group('path'))
        )

class DigestLineFormats(object):
    """
    Implements a simple mechanism to guess whether a digest line is in GNU
    coreutils or reverse BSD format.
    """

    COREUTILS = DigestLineFormatCoreutils()
    BSD_REVERSED = DigestLineFormatBSDReversed()

    candidates = [COREUTILS, BSD_REVERSED]

    def guess(self, buf: io.BufferedReader):
        """
        Returns either DigestLineFormats.COREUTILS or
        DigestLineFormats.REVERSE_BSD
        """
        for candidate in self.candidates:
            if candidate.match(buf):
                return candidate
        else:
            raise DigestFormatError('Failed to detect GNU coreutils or '
                                    'reverse BSD line format')

class DigestParser(object):
    """
    Parse digest files in coreutils md5sum / shasum and BSD reversed format.

    Files are expected to be in the format <digest>{space}<flag><path> where
    <digest> represents the md5 / sha hex digest, <flag> is either a space
    character (text mode) or an asterisk (binary mode) and <path> is the path
    to the file. Note: reversed BSD format lacks the flag column.
    """

    def parse(
        self,
        lines,
        filefmt: DigestFileFormat = DigestFileFormats.NATIVE,
        linefmt: DigestLineFormat = DigestLineFormats.COREUTILS
    ):
        """
        Iterates through the list of lines and yields a DigestEntry for each of
        them. Throws a RuntimeException if a line does not match the expected
        format.
        """
        for line in lines:
            yield linefmt.parse(line, filefmt)


class DigestList(object):
    """
    Iterate through a list of coreutils digest files.
    """

    def __init__(self,
                 flat=False,
                 flag=None,
                 parser: DigestParser = DigestParser(),
                 filefmts: DigestFileFormats = DigestFileFormats(),
                 linefmts: DigestLineFormats = DigestLineFormats()):
        self.flat = flat
        self.flag = flag
        self.parser = parser
        self.filefmts = filefmts
        self.linefmts = linefmts

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
                    filefmt = self.filefmts.guess(buf)
                    linefmt = self.linefmts.guess(buf)
                    entries = self.parser.parse(
                        filefmt.text(buf),
                        filefmt,
                        linefmt
                    )
                    for entry in entries:
                        yield DigestEntry(
                                digest=entry.digest,
                                flag=entry.flag if self.flag is None else self.flag,
                                path=entry.path if self.flat else dirname / entry.path)
                except DigestFormatError as e:
                    raise DigestFileError(f'Failed while opening "{dgstfile}", {e}') from e
                except DigestParserError as e:
                    raise DigestFileError(f'Failed while parsing "{dgstfile}", {e}') from e
