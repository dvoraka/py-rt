[![Build Status](https://travis-ci.org/dvoraka/py-rt.svg?branch=master)](https://travis-ci.org/dvoraka/py-rt)

# Introduction

Python library for Request Tracker (http://bestpractical.com/rt/) using REST API.

## Examples:
```
>>> import pyrt
>>> rt = pyrt.RT4('http://localhost/rt/REST/1.0/')
>>> rt.login('user', 'pass')
>>> tickets = rt.search_ticket('Queue="General"')
>>> print(tickets)
Ticket list: 4 tickets
>>> for ticket in tickets.list_all():
        print(ticket)
(1, u'First ticket')
(3, u'test1')
(2, u'Problem')
(5, u'Help me!')

```
