#!/usr/bin/env python3

import os
import csv
import dotenv
import bleach
import pypandoc
import airtable

dotenv.load_dotenv()

base = os.environ['AIRTABLE_BASE']
key = os.environ['AIRTABLE_KEY']
table = airtable.Airtable(base, 'Bio Import', key)

for row in csv.DictReader(open('events-speaker-html.csv')):
    html = row['speaker_bio']
    html = html.replace('_x000D_', ' ')
    html = bleach.clean(html, tags=['b', 'em', 'a', 'strong', 'i'])
    bio = pypandoc.convert_text(html, 'md', format='html')

    pypandoc.convert_text(row['speaker_bio'], 'md', format='html')
    table.insert({
        'full name': row['speaker_name'],
        'first name': row['first name'],
        'last name': row['last name'],
        'bio': bio
    })
