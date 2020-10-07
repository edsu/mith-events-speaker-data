#!/usr/bin/env python3

import csv
import pypandoc

data_in = csv.reader(open('events-speaker-html.csv'))
data_out = csv.writer(open('event-speaker-md.csv', 'w'))

col_headers = next(data_in)
data_out.writerow(col_headers)

for row in data_in:
    html = row[8]
    rtf = pypandoc.convert_text(html, 'md', format='html')
    row[8] = rtf
    data_out.writerow(row)
