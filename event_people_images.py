#!/usr/bin/env python3

import os
import re
import shutil
import dotenv
import pathlib
import airtable

from collections import defaultdict
from xml.etree import ElementTree as etree

dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_API_KEY')

people_base = os.environ.get('AIRTABLE_PEOPLE_BASE_ID')
people_table = airtable.Airtable(people_base, 'People', key)
people = people_table.get_all()

ns = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/"
}

def normal_name(s):
    if s == None:
        return None
    else:
        return re.sub(r'[^\w]', '', s.lower())


# mapping of names to filenames
tree = etree.parse('wp-mith.xml')
root = tree.getroot()

name_images = {}
for e in root.findall('./channel/item'):
    post_id = e.find('wp:post_id', ns).text
    post_title = e.find('title').text
    post_name = e.find('wp:post_name', ns).text
    post_type = e.find('wp:post_type', ns).text

    if post_type != 'attachment':
        continue

    post_meta = defaultdict(list)
    for pm in e.findall('wp:postmeta', ns):
        k = pm.find('wp:meta_key', ns).text
        v = pm.find('wp:meta_value', ns).text
        post_meta[k].append(v)

    if '_wp_attached_file' not in post_meta:
        continue


    filename = None
    for f in post_meta['_wp_attached_file']:
        if pathlib.Path(f).suffix.lower() in ['.jpg', '.gif', '.png', 'jpeg']:
            filename = f

    if not filename:
        continue

    name = normal_name(post_title)
    if name and filename:
        name_images[name] = filename

    alt = post_meta.get('_wp_attachment_image_alt')
    if alt and alt[0] != None and filename:
        name_images[normal_name(alt[0])] = filename


found = 0
count = 0
for person in people:
    if 'headshot' not in person['fields']:
        found_image = None
        count += 1

        name = person['fields']['name']
        name_norm = normal_name(name)
        if name_norm in name_images:
            found_image = name_images[name_norm]
        else:
            for k, v in name_images.items():
                if name_norm in k:
                    found_image = name_images[k]
                    break

        if found_image is not None:
            found += 1
            src = pathlib.Path('wordpress/mith.umd.edu/wp-content/uploads') / found_image
            dst = pathlib.Path('uploads') / found_image
            if not dst.parent.exists():
                dst.parent.mkdir(parents=True)
            if not dst.exists():
                shutil.copyfile(src, dst)
            url = 'https://raw.githubusercontent.com/edsu/mith-static-munging/master/uploads/' + found_image 
            print(name, url)
            people_table.update(person['id'], {'headshot': [{'url': url}]})


