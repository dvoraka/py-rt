#! /usr/bin/env python

import pyrt

# set URL and credentials
rt = pyrt.RT4('http://localhost/rt/REST/1.0/')
rt.login('user', 'pass')

# search and print info
tl = rt.search_ticket('Queue="General"')
print(tl)

# list found tickets
print('Tickets:')
for t in tl.list_all():
    print(t)

# get ticket with id 2
ticket = rt.get_ticket('2')
print(ticket)

# create ticket
print('Creating ticket...')
reply = rt.create_ticket({'content': 'Queue: General\nSubject: Help me'})
print(reply)
