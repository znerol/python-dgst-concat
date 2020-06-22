Digest Concat
=============

A collection of python 3 scripts to collect and concatenate coreutils digest
files.


Usage
-----

dgst-concat.py
==============

```
usage: dgst-concat.py [-h] [-d] [-o OUTFILE] [-b | -t] PATTERN [PATTERN ...]

Recursively concatenate coreutils digest files.

positional arguments:
  PATTERN               glob pattern for digest files. E.g., "**/*.md5"

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           print a stacktrace when something goes wrong
  -o OUTFILE, --outfile OUTFILE
                        output file, defaults to standard output
  -b, --binary          enforce binary tag (i.e., add a * in front of each entry)
  -t, --text            enforce text tag (i.e., clear any * in front of each entry)
```

dgst-concat-dir.py
==================

```
usage: dgst-concat-dir.py [-h] [-d] [-o OUTNAME] [-b | -t] PATTERN [PATTERN ...]

Recursively walk a filesystem hierarchy and concatenate digest files into one file per directory.

positional arguments:
  PATTERN               glob pattern for digest files. E.g., "*.md5"

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           print a stacktrace when something goes wrong
  -o OUTNAME, --outname OUTNAME
                        output file name
  -b, --binary          enforce binary tag (i.e., add a * in front of each entry)
  -t, --text            enforce text tag (i.e., clear any * in front of each entry)
```

License
-------

Digest concat source code is in the [public-domain](LICENSE) and is free to everyone to use for any purpose.
