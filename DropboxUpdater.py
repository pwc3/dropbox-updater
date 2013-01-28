#!/usr/bin/env python

# Copyright (c) 2013, Paul Calnan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of the author nor the names of its contributors may be
#   used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import argparse
import os
import plistlib
import subprocess
import sys
import time
import urllib2
import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    print >>sys.stderr, '\n'.join((
        "Error: This script requires the beautifulsoup4 module",
        "It can be installed with easy_install or pip.",
        "    easy_install beautifulsoup4",
        "    pip install beautifulsoup4",
    ))
    sys.exit(1)

## Constants ##################################################################

# This script scrapes values from a website. As such, it makes several
# assumptions about page layout and file locations. I tried to capture them all
# here.

# Assumption: this is the correct base URL for downloads
# Assumption: the DMG filename is "Dropbox $VERSION_NUMBER"
DEFAULT_BASE_URL = 'https://dl-web.dropbox.com/u/17/Dropbox'

# Assumption: this is where Dropbox is installed
DEFAULT_DROPBOX_APP_PATH = '/Applications/Dropbox.app'

# Assumption: this page contains the latest version number in a
# <span id="version_str"> tag.
DEFAULT_INSTALL_PAGE_URL = 'https://www.dropbox.com/install'

# Assumption: after mounting the DMG, the installer is located here
INSTALLER_PATH = '/Volumes/Dropbox Installer/Dropbox.app'

# Use Safari's user agent so the server will give us a Mac version
SAFARI_USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) '
                     'AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 '
                     'Safari/536.26.17')

# HACK: Delay in seconds between opening the DMG and when the installer is
# accessed. Increase this value if the installer isn't found.
SECONDS_TO_WAIT_FOR_DMG = 5

## Functions ##################################################################

def get_installed_version(dropbox_app_path=DEFAULT_DROPBOX_APP_PATH):
    """Returns the CFBundleVersion value in the Info.plist file in the app at
    `dropbox_app_path`.

    """
    plist_path = os.path.join(dropbox_app_path, 'Contents', 'Info.plist')
    plist = plistlib.readPlist(plist_path)
    return plist['CFBundleVersion']

def get_latest_available_version(install_page_url=DEFAULT_INSTALL_PAGE_URL):
    """Downloads the HTML file at `install_page_url` and scrapes the app
    version. We assume that there is a <span id="version_str"> tag that
    contains the latest version number, followed by the string " for Mac".
    Returns the scraped version number.

    """
    request = urllib2.Request(install_page_url)

    # set the user agent to Safari for OS X to ensure we get the Mac version
    request.add_header('User-Agent', SAFARI_USER_AGENT)

    # download the HTML
    opener = urllib2.build_opener()
    html = opener.open(request).read()

    # scrape the HTML
    soup = BeautifulSoup(html)

    # find a <span> with an ID of "version_str"
    for span in soup.find_all('span'):
        if span.get('id') == 'version_str':
            return span.text.replace(' for Mac', '')

    raise ValueError('Could not find version_str in %s' %
                     DEFAULT_INSTALL_PAGE_URL)

def download_version(version_number, base_url=DEFAULT_BASE_URL):
    """Downloads the specified version from the specified base URL.

    """
    dmg_filename = 'Dropbox %s.dmg' % version_number
    url = urlparse.urljoin(base_url, dmg_filename)

    unexpanded = os.path.join('~/Downloads', os.path.basename(url))
    output_filename = os.path.expanduser(unexpanded)

    print "Downloading", url, "to", unexpanded
    response = urllib2.urlopen(url)
    with open(output_filename, "wb") as fh:
        fh.write(response.read())

    return output_filename

def install_from(dmg_path):
    """Mounts the specified DMG file and launches the installer.

    """
    # open the DMG file
    print "Opening downloaded DMG file", dmg_path
    subprocess.check_call(['open', dmg_path])

    # wait for the DMG to mount
    print "Waiting for DMG to mount"
    time.sleep(SECONDS_TO_WAIT_FOR_DMG)

    # open (launch) the installer
    print "Launching installer at", INSTALLER_PATH
    subprocess.check_call(['open', INSTALLER_PATH])

## Command-Line Interface #####################################################

def parse_args(argv):
    """Parses command line arguments.

    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Dropbox app updater")
    parser.add_argument('-v', '--version',
                        required=False,
                        help="force install the specified version")
    parser.add_argument('-d', '--dry-run',
                        required=False,
                        default=False,
                        action='store_true',
                        help="download but do not actually install anything")
    return parser.parse_args(argv)

def main(argv=None):
    # parse the command-line arguments
    options = parse_args(argv)

    # find the installed version of the software
    installed = get_installed_version()
    print 'Installed version:', installed

    # if the user wants a specific version...
    if options.version:
        try:
            # ...download it
            downloaded = download_version(options.version)

            # install if we're not doing a dry run
            if options.dry_run:
                print "Dry run. Skipping installation of", downloaded
            else:
                install_from(downloaded)
        except Exception as err:
            print 'Could not install version %s: %s' % (options.version, err)
            return 1

    else:
        # find the latest available version
        try:
            available = get_latest_available_version()
            print 'Latest available version:', available
        except Exception as err:
            print 'Could not determine latest available version: %s' % err
            return 1

        # if an update is available...
        if installed < available:
            # ...download it
            print 'Update is available'
            downloaded = download_version(available)

            # install if we're not doing a dry run
            if options.dry_run:
                print "Dry run. Skipping installation of", downloaded
            else:
                install_from(downloaded)

        elif installed > available:
            print 'Running forum build greater than general release version'
        else:
            print 'Up to date'

if __name__ == "__main__":
    sys.exit(main())
