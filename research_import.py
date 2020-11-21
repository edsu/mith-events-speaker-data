#!/usr/bin/env python3

"""
Loading research markdown into Airtable.
"""

import os
import re
import bs4
import bleach
import dotenv
import urllib
import pathlib
import wayback
import airtable
import pypandoc
import requests_html

from shutil import copyfile

# get the airtable credentials
dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_API_KEY')
base_id = os.environ.get('AIRTABLE_RESEARCH_BASE_ID')
projects = airtable.Airtable(base_id, 'Projects', key)

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

# a function to try to get the description for a slug as markdown
# it will look in a variety of places in both our archive and the Internet
# Archive

def get_description(slug):

    # look for the digital dialogue in MITH archive
    url = 'https://archive.mith.umd.edu/mith-2020/research/' + slug + '/'
    resp = http.get(url)
    description = resp.html.find('.research-content', first=True)

    # look for the research post at the Internet Archive
    if not description:
        url = 'https://mith.umd.edu/research/' + slug + '/'
        resp = wayback_search(url)
        if resp:
            description = resp.html.find('.research-content', first=True)

    # look for the blog post in MITH archive
    if not description:
        url = 'https://archive.mith.umd.edu/mith-2020/' + slug + '/'
        resp = http.get(url)
        description = resp.html.find('.post', first=True)

    # look for the blog post at the Internet Archive
    if not description:
        url = 'https://mith.umd.edu/' + slug + '/'
        resp = wayback_search(url)
        if resp:
            description = resp.html.find('.research-content', first=True)

    if not description:
        return None, None

    img = resp.html.find('.slides img', first=True)
    if img:
        img = urllib.parse.urljoin(url, img.attrs['src'])

    html = description.html
    open('out/{}.html'.format(slug), 'w').write(html)

    html = html.replace('_x000D_', ' ')
    html = html.replace('\n', ' ')
    html = re.sub('\xa0', ' ', html)
    html = re.sub('  +', ' ', html)

    # remove project metadata since we have it in airtable
    html = re.sub('<div class="fusion-meta-info">.+$', '', html)

    html = bleach.clean(html, tags=['h1', 'h2', 'h3', 'h4', 'span', 'p', 'ul', 'li', 'b', 'em', 'a', 'strong', 'i'], strip=True)
    html = re.sub(r'<div>', '<p>', html)
    html = re.sub(r'</div>', '</p>', html)
    
    md = pypandoc.convert_text(html, 'md', format='html', extra_args=['--wrap', 'preserve'])
    open('out/{}.md'.format(slug), 'w').write(md)

    return img, md

for p in projects.get_all():
    rec_id = p['id']
    slug = p['fields'].get('id')
    img, md = get_description(slug)

    if md:
        projects.update(rec_id, {"description": md})
        print('+ {}'.format(slug))
    else:
        print('- {}'.format(slug))   

    if img:
        resp = http.get(img)
        if resp.status_code == 200:
            projects.update(rec_id, {"image": [{'url': img}]})
            print('+ {} {}'.format(slug, img))
    else:
        print('- {} {}'.format(slug, img))
