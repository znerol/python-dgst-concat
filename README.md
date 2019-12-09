Digest Concat
=============

A python 3 script to collect and concatenate coreutils digest files.


Usage
-----

```
usage: dgst-concat.py [-h] [-o [OUTFILE]] PATTERN [PATTERN ...]

Recursively concatenate coreutils digest files.

positional arguments:
  PATTERN               glob pattern for digest files. E.g., "**/*.md5"

optional arguments:
  -h, --help            show this help message and exit
  -o [OUTFILE], --outfile [OUTFILE]
                        output file, defaults to standard output
```


License
-------

Digest concat source code is in the [public-domain](LICENSE) and is free to everyone to use for any purpose. 
