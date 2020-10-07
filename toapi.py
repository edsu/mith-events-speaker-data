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
table = airtable.Airtable(base, 'Bio Import', key)

rows = []
for row in csv.DictReader(open('events-speaker-html.csv')):
    html = row['speaker_bio']
    html = html.replace('_x000D_', ' ')
    html = html.replace('\n', ' ')
    html = re.sub('\xa0', ' ', html)
    html = re.sub('  +', ' ', html)
    html = bleach.clean(html, tags=['b', 'em', 'a', 'strong', 'i'], strip=True)

    bio = pypandoc.convert_text(html, 'md', format='html')
    bio = bio.replace('\n', ' ')

    table.insert({
        'full name': row['speaker_name'],
        'first name': row['first name'],
        'last name': row['last name'],
        'bio': bio
    })
