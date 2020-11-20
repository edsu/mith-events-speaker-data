#!/usr/bin/env python3

import os
import dotenv
import pathlib
import airtable

from shutil import copyfile
from collections import defaultdict
from xml.etree import ElementTree as etree


# get the airtable credentials

dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_KEY')
people = airtable.Airtable('appk2btw36qEO3vFo', 'People', key) 


# parse the wordpress xml looking for mith_person headshots

ns = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/"
}

tree = etree.parse('wp-mith.xml')
root = tree.getroot()

# a mapping of people names (slugs) to attachment ids
name_attachids = {}

# a mapping of attachment ids to filenames
attachid_filenames = {}

for e in root.findall('./channel/item'):
    post_id = e.find('wp:post_id', ns).text
    post_name = e.find('wp:post_name', ns).text
    post_type = e.find('wp:post_type', ns).text

    if post_type not in ['mith_person', 'attachment']:
        continue

    post_meta = defaultdict(list)
    for pm in e.findall('wp:postmeta', ns):
        k = pm.find('wp:meta_key', ns).text
        v = pm.find('wp:meta_value', ns).text
        post_meta[k].append(v)

    if post_type == 'mith_person' and '_thumbnail_id' in post_meta:
        name_attachids[post_name] = post_meta['_thumbnail_id'][0]
    elif post_type == 'attachment' and '_wp_attached_file' in post_meta:
        attachid_filenames[post_id] = post_meta['_wp_attached_file'][0]

wp_uploads = pathlib.Path('wordpress/mith.umd.edu/wp-content/uploads/')
new_wp_uploads = pathlib.Path('wp-uploads')
name_thumburls = {}

for name, attach_id in name_attachids.items():
    relpath = attachid_filenames[attach_id]
    orig = wp_uploads / relpath
    thumb = new_wp_uploads / relpath

    if not thumb.parent.exists():
        thumb.parent.mkdir(parents=True)

    copyfile(orig, thumb)
    url = 'https://raw.githubusercontent.com/edsu/mith-static-munging/master/' + relpath 
    name_thumburls[name] = url

# update airtable by posting the url for the image

for p in people.get_all():
    name = p['fields']['id']
    if name in name_thumburls:
        thumb_url = name_thumburls[name]
        print(name, thumb_url)
