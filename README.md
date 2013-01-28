Dropbox Updater for Mac OS X
============================

Since the Dropbox client software installed on my computer never seems to
automatically update, I wrote this script to do it for me. It was developed and
tested under Mac OS X Mountain Lion 10.8.2.

The script does the following:

1. Checks `/Applications/Dropbox.app` for the currently-installed version
   number.
2. Checks [http://www.dropbox.com/install](http://www.dropbox.com/install) for
   the "latest available version" (i.e., whichever version is listed on the
   *Download* button, which may not, in fact, be the latest available version).
3. If the installed version number is less than the "latest available version",
   it attempts to download a DMG file to `~/Downloads`.
4. If a DMG was successfully downloaded, the script then mounts the DMG and
   runs the installer.

There are several assumptions made in the script. I tried to document them all
and use easily-modifiable constants wherever possible. If the script fails, one
of the assumptions may no longer be valid.

There are two command-line options (run with `--help` for details). The
`-v`/`--version` option allows you to specify the version to install. This is
useful when installing Forum builds. The `-d`/`--dry-run` option performs a
"dry run" which downloads the DMG but does not mount it or run the installer.

The script requires the `beautifulsoup4` module. It is used to scrape the
Dropbox download page to determine the version number. It can be installed via
either `pip install beautifulsoup4` or `easy_install beautifulsoup4`.
