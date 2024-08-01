#!/usr/bin/env python3

"""link_checker.py -- checks the links in README.txt and documentation."""

import os
import re
import sys
import urllib.request
import urllib.error


scriptdir = os.path.dirname(os.path.abspath(__file__))
dhparserdir = os.path.abspath(os.path.join(scriptdir, os.pardir))
if dhparserdir not in sys.path:
    sys.path.append(dhparserdir)
os.chdir(dhparserdir)

docdir = "documentation_src"
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0'
RX_URL = re.compile(r'https?://[^\s>)"]+')


def gather_docs():
    paths = []
    for root, dirs, files in os.walk(os.path.join(dhparserdir, docdir)):
        for f in files:
            if f.endswith('.rst') or f.endswith('.md'):
                paths.append(os.path.join(root, f))
    for f in os.listdir(dhparserdir):
        if f.endswith('.rst') or f.endswith('.md'):
            paths.append(os.path.join(dhparserdir, f))
    for root, dirs, files in os.walk(os.path.join(dhparserdir, 'DHParser')):
        for f in files:
            if f.endswith('.py') or f.endswith('.pyi'):
                paths.append(os.path.join(root, f))
    return paths


def find_urls_in_file(fname):
    with open(fname) as f:
        text = f.read()
    return RX_URL.findall(text)


def check_link(url):
    handle = None
    request = urllib.request.Request(url, headers={'User-Agent': user_agent})
    try:
        handle = urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as e:
        return str(e)
    except urllib.error.URLError as e:
        return str(e)
    if handle:
        handle.close()
    return "ok"


def check_urls(urls, indent=4, cache=None):
    if cache is None:
        cache = dict()
    tab = " " * indent
    errors = 0
    for url in urls:
        result = cache.setdefault(url, check_link(url))
        if result != 'ok':
            errors += 1
        output = [tab, url, " ", result]
        print(''.join(output))
    return errors


def check_links_in_docs():
    errors = 0
    cache = dict()
    paths = gather_docs()
    for path in paths:
        urls = find_urls_in_file(path)
        if urls:
            print(path)
            errors += check_urls(urls, cache=cache)
    print(f'{errors} errors were found.')


if __name__ == '__main__':
    check_links_in_docs()



