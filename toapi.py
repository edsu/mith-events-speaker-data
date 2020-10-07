#!/usr/bin/env python3

import os
import re
import csv
import dotenv
import bleach
import pypandoc
import airtable

dotenv.load_dotenv()

base = os.environ['AIRTABLE_BASE']
key = os.environ['AIRTABLE_KEY']
table = airtable.Airtable(base, 'Speaker(s)', key)

# create a mapping of names to row ids
name_ids = {r['fields']['speaker name']: r['id'] for r in table.get_all()}

for row in csv.DictReader(open('events-speaker-html.csv')):

    # clean the speaker bio html
    html = row['speaker_bio']
    html = html.replace('_x000D_', ' ')
    html = html.replace('\n', ' ')
    html = re.sub('\xa0', ' ', html)
    html = re.sub('  +', ' ', html)
    html = bleach.clean(html, tags=['b', 'em', 'a', 'strong', 'i'], strip=True)

    # convert html to markdown
    bio = pypandoc.convert_text(html, 'md', format='html')
    bio = bio.replace('\n', ' ')

    # figure out the row id for the name
    name = row['speaker_name']
    row_id = name_ids.get(name)

    # update the correct row with the markdown speaker bio
    if row_id:
        table.update(row_id, {'speaker bio': bio})
    else:
        print('no row for {}'.format(name))
