#!/usr/bin/env python3

"""
Loading events markdown into Airtable.
"""

import os
import re
import bs4
import bleach
import dotenv
import wayback
import airtable
import pypandoc
import requests_html

# get the airtable credentials
dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_KEY')
events = airtable.Airtable('appTv9J1zxqaNgBHi', 'Events', key)

# a web client
http = requests_html.HTMLSession()

# a function to return the first wayback archive for a url

wb = wayback.WaybackClient()
def wayback_search(url):
    try:
        memento = next(wb.search(url))
        resp = http.get(memento.raw_url)
        return resp
    except StopIteration:
        return None

# a function to try to get the abstract for a slug as markdown
# it will look in a variety of places in both our archive and the Internet
# Archive

def get_abstract(slug):

    # look for the digital dialogue in MITH archive
    url = 'https://archive.mith.umd.edu/mith-2020/dialogues/' + slug + '/'
    resp = http.get(url)
    abstract = resp.html.find('.abstract', first=True)

    # look for a research path in MITH archive
    if not abstract:
        url = 'https://archive.mith.umd.edu/mith-2020/research/' + slug + '/'
        resp = http.get(url)
        abstract = resp.html.find('.post', first=True)

    # look for the blog post in MITH archive
    if not abstract:
        url = 'https://archive.mith.umd.edu/mith-2020/' + slug + '/'
        resp = http.get(url)
        abstract = resp.html.find('.post', first=True)

    # look for the digital dialogue at the Internet Archive
    if not abstract:
        url = 'https://mith.umd.edu/dialogues/' + slug + '/'
        resp = wayback_search(url)
        if resp:
            print('wb-dd', url)
            abstract = resp.html.find('.abstract', first=True)

    # look for the research post at the Internet Archive
    if not abstract:
        url = 'https://mith.umd.edu/research/' + slug + '/'
        resp = wayback_search(url)
        if resp:
            print('wb-research', url)
            abstract = resp.html.find('.post', first=True)

    # look for the blog post at the Internet Archive
    if not abstract:
        url = 'https://mith.umd.edu/' + slug + '/'
        resp = wayback_search(url)
        if resp:
            print('wb-blog', url)
            abstract = resp.html.find('.post', first=True)

    if not abstract:
        return None

    html = abstract.html
    html = html.replace('_x000D_', ' ')
    html = html.replace('\n', ' ')
    html = re.sub('\xa0', ' ', html)
    html = re.sub('  +', ' ', html)
    html = bleach.clean(html, tags=['b', 'em', 'a', 'strong', 'i'], strip=True)

    md = pypandoc.convert_text(html, 'md', format='html')
    return md

for e in events.get_all():
    rec_id = e['id']
    slug = e['fields'].get('ID')
    md = get_abstract(slug)

    if md:
        print('+ {}'.format(slug))
        events.update(rec_id, {"description": md})
    else:
        print('- {}'.format(slug))

