#!/usr/bin/env python

"""
Loading events markdown into Airtable.
"""

import os
import re
import json
import bleach
import dotenv
import shutil
import airtable
import requests
import pypandoc
import fusionbuilder
import xml.etree.ElementTree as etree

from pathlib import Path

# map of file extensions to typed directories

dir_map = {
    ".csv": "data",
    ".dmg": "data",
    ".gif": "images",
    ".jpeg": "images",
    ".jpg": "images",
    ".json": "data",
    ".key": "docs",
    ".m4v": "video",
    ".mp3": "audio",
    ".pdf": "docs",
    ".png": "images",
    ".ppt": "docs",
    ".pptx": "docs",
    ".xml": "docs",
    ".zip": "data"
}

site_backup = Path('wordpress/mith.umd.edu/wp-content/uploads/')

def rewrite_upload(url):
    new_url = url
    m = re.match(r'https://mith.umd.edu/wp-content/uploads/(.+)', url)
    if m:
        path = Path(m.group(1))
        ext = path.suffix.lower()

        new_path = Path(dir_map[ext]) / path.as_posix().replace('/', '-')
        site_path = Path('site') / new_path

        if not site_path.parent.exists():
            site_path.parent.mkdir()

        if not site_path.exists():
            shutil.copyfile(site_backup / path, site_path)

        new_url = 'https://mith.umd.edu/' + new_path.as_posix()

    return new_url

def rewrite_uploads(text):
    return re.sub(
        r'"https://mith.umd.edu/wp-content/uploads/(.+?)"', 
        lambda m: '"' + rewrite_upload(m.group(1)) + '"',
        text 
    )

# airtable credentials

dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_KEY')

# parse the wordpress export and create a few mappings of things 

content = {}
slug_ids = {}
attachments = {}

tree = etree.parse('wp-mith.xml')
root = tree.getroot()

ns = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/"
}

items = {}
attachments = {}

for e in root.findall('./channel/item'):
    post_name = e.find('wp:post_name', ns).text
    post_id = e.find('wp:post_id', ns).text
    post_type = e.find('wp:post_type', ns).text
    post_content = e.find('content:encoded', ns).text

    post_meta = {}
    for pm in e.findall('wp:postmeta', ns):
        k = pm.find('wp:meta_key', ns).text
        v = pm.find('wp:meta_value', ns).text
        if v is None:
            continue
        if k in post_meta:
            post_meta[k].append(v)
        else:
            post_meta[k] = [v]

    items[post_id] = {
        "id": post_id,
        "name": post_name,
        "content": post_content,
        "meta": post_meta,
        "type": post_type
    }

    # extra look up by slug for these post types
    if post_type in ["mith_dialogue", "mith_research", "post"]:
        items[post_name] = items[post_id]

    # attachments get an extra metadata value and a mapping
    # from the parent item id to the item id so they can be 
    # looked up later
    if post_type == "attachment":
        attachment_url = e.find('wp:attachment_url', ns).text
        items[post_id]['attachment_url'] = attachment_url

        parent_id = e.find('wp:post_parent', ns).text
        if parent_id in attachments:
            attachments[parent_id].append(post_id)
        else:
            attachments[parent_id] = [post_id]

def id2link(id):
    """
    Convert a post_id to the url for an attachment. And save the file from
    the archive.
    """
    if id in items and items[id]['attachment_url']:
        url = items[id]['attachment_url']
        url = rewrite_upload(url)
        return url
    return id

# get the events table

events_table = airtable.Airtable('appTv9J1zxqaNgBHi', 'Events', key)
events = events_table.get_all()

# examine each event and upload the markdown as the description

for e in events:
    id = e['id']
    slug = e['fields'].get('ID')

    if slug in items:
        item = items[slug]
        html = item['content']

        root, html = fusionbuilder.parse(html)

        html = html.replace('_x000D_', ' ')
        html = html.replace('\n', ' ')
        html = re.sub('\xa0', ' ', html)
        html = re.sub('  +', ' ', html)
        html = bleach.clean(html, tags=['b', 'em', 'a', 'strong', 'i'], strip=True)

        md = pypandoc.convert_text(html, 'md', format='html')

        rec = {
            'description_new': md,
        }


        for key, values in item['meta'].items():
            if key == '_thumbnail_id':
                rec['image_link'] = id2link(values[0])

        # xxx: bring this back if we need to process all the files
        # and remove the three lines above 

        '''

        # parent attachments

        for attach_id in attachments.get(item['id'], []):
            attach = items[attach_id]
            url = rewrite_upload(attach['attachment_url'])
            if 'mith.umd.edu/images/' in url:
                rec['image_link'] = url
            else:
                rec['file_link'].append(url)

        # also look for files in metadata, not all are linked via parent

        for key, values in item['meta'].items():
            if key == '_thumbnail_id':
                rec['image_link'].extend(map(id2link, values))
            elif re.match('dialogue_files_\d+_dialogue_file_obj', key):
                rec['file_link'].extend(map(id2link, values))
            elif re.match('dialogue_files_\d+_dialogue_file_url', key):
                rec['file_link'].extend(map(rewrite_upload, values))

        # make them unique

        rec['image_link'] = list(set(rec['image_link']))

        rec['file_link'] = list(set(rec['file_link']))
        '''

        print(rec)

        events_table.update(id, rec)
