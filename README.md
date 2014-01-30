py-rt
=====

Library for Request Tracker (http://bestpractical.com/rt/) using REST API.

Examples:
```
>>> import pyrt
>>> rt = pyrt.RT4('http://localhost/rt/REST/1.0/')
>>> rt.login('user', 'pass')
>>> tickets = rt.search_ticket('Queue="General"')
>>> print(tickets)
Ticket list: 5 tickets
>>> for t in tickets.list_all():
        print(t)
(1, u'First ticket')
(3, u'test1')
(2, u'Problem')
(5, u'Help me!')

```
