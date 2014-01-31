# *-* encoding: utf-8 *-*

from __future__ import unicode_literals
from __future__ import print_function

import unittest
import pyrt


class TestTicket(unittest.TestCase):

    def setUp(self):

        pass

    def test_init(self):

        with self.assertRaises(TypeError):

            ticket = pyrt.Ticket(
                '+ěščřž',
                '+ěščřž',
                {'žř': 'žř'},
                None,
            )

        ticket = pyrt.Ticket(
            '+ěščřž',
            '+ěščřž',
            {'žř': 'žř'},
            pyrt.RT4('čřčřč'),
        )

    def test_map_data(self):
        
        ticket = pyrt.Ticket(
            '+ěščřž',
            '+ěščřž',
            {'žř': 'žř'},
            pyrt.RT4('čřčřč'),
        )

        data = {'+ěščřž': '+ěščřž'}
        ticket.map_data(data)


class TestTicketHistory(unittest.TestCase):
    
    def setUp(self):

        self.th = pyrt.TicketHistory(None, None)


class TestTicketList(unittest.TestCase):

    def setUp(self):

        data = {
                '10': 'Test 1',
                '25': 'test 2',
                '222555': 'Very long subject',
                'five': 'test',
                '1': 'text',
                '2': '+ěščřž',
        }

        self.tl = pyrt.TicketList(data, pyrt.RT4())

    def test_list_all(self):
        
        out = self.tl.list_all()
        aout = (
            (10, 'Test 1'),
            (25, 'test 2'),
            (222555, 'Very long subject'),
            (1, 'text'),
            (2, '+ěščřž'),
        )

        self.assertItemsEqual(out, aout)


class TestRT4(unittest.TestCase):

    def setUp(self):

        self.rt = pyrt.RT4()
   
    def test_login(self):
        
        self.rt.login('test', 'testpass')
        aout = {'user': 'test', 'pass': 'testpass'}
        self.assertEqual(self.rt.credentials, aout)

        self.rt.login('test login', 'test pass')
        aout = {'user': 'test login', 'pass': 'test pass'}
        self.assertEqual(self.rt.credentials, aout)

    def test_check_reply(self):

        text = ''
        reply = self.rt.check_reply(text)
        self.assertEqual(reply, '')

        text = 'RT/4.0 200 ok\n'
        reply = self.rt.check_reply(text)
        self.assertEqual(reply, '\n')

        text = 'RT/4.0 200 ok\n\nNo matching results.\n'
        reply = self.rt.check_reply(text)
        self.assertEqual(reply, 'No matching results.\n')

        with self.assertRaises(pyrt.BadRequestException):

            text = 'RT/4.0 400 Bad request\n'
            reply = self.rt.check_reply(text)

        with self.assertRaises(pyrt.BadRequestException):

            text = 'RT/4.0 400 Bad request\n\nReason:\n'
            reply = self.rt.check_reply(text)

    def test_history_id(self):
        
        text = 'test'
        reply = self.rt._history_id(text)
        self.assertEqual(reply, None)

        text = 't: 10'
        reply = self.rt._history_id(text)
        self.assertEqual(reply, None)

        text = 'id: 10'
        reply = self.rt._history_id(text)
        self.assertEqual(reply, '10')

        text = 'id: 12345678901234567890'
        reply = self.rt._history_id(text)
        self.assertEqual(reply, '12345678901234567890')

        text = 'id: test'
        reply = self.rt._history_id(text)
        self.assertEqual(reply, None)

        text = ':test\nid: 10\n::'
        reply = self.rt._history_id(text)
        self.assertEqual(reply, '10')

        text = ''
        reply = self.rt._history_id(text)
        self.assertEqual(reply, None)

    def test_parse_reply(self):
        
        text = ''
        reply = self.rt.parse_reply(text)
        self.assertEqual(reply, None)

        text = 'RT/4.0 200 ok\n'
        reply = self.rt.parse_reply(text)
        self.assertEqual(reply, {})

        text = 'RT/4.0 200 ok\n\nNo matching results.\n'
        reply = self.rt.parse_reply(text)
        self.assertEqual(reply, {})

        text = 'RT/4.0 200 ok\n\n# test text\n'
        reply = self.rt.parse_reply(text)
        self.assertEqual(reply, {})

        text = 'RT/4.0 200 ok\n\nTestfield: test\n'
        reply = self.rt.parse_reply(text)
        areply = {'Testfield': 'test'}
        self.assertEqual(reply, areply)

        text = 'RT/4.0 200 ok\n\n\n\n\n\nTestfield: test\n\n\n'
        reply = self.rt.parse_reply(text)
        areply = {'Testfield': 'test'}
        self.assertEqual(reply, areply)

        text = 'RT/4.0 200 ok\n\nTestfield: test\nId: 10\n'
        reply = self.rt.parse_reply(text)
        areply = {'Testfield': 'test', 'Id': '10'}
        self.assertEqual(reply, areply)

        with self.assertRaises(pyrt.BadRequestException):

            text = 'RT/4.0 400 Bad request\n'
            reply = self.rt.parse_reply(text)

        with self.assertRaises(pyrt.BadRequestException):

            text = 'RT/4.0 400 Bad request\n\nReason:\n'
            reply = self.rt.parse_reply(text)

    def test_parse_history_reply(self):
        
        text = ''
        out = self.rt.parse_history_reply(text)
        aout = None
        self.assertEqual(out, aout)
 
        text = ('RT/4.0 200 ok\n\nid: 10\n\nTicket: 1234567890\n'
            'Type: Create\nCreator: tuser\n'
            'Description: Correspondence\n'
            'Created: 2013-06-20 06:35:11\n'
        )
        out = self.rt.parse_history_reply(text)
        aout = {'10': {'id': '10',
            'Ticket': '1234567890', 'Type': 'Create',
            'Creator': 'tuser',
            'Description': 'Correspondence',
            'Created': '2013-06-20 06:35:11',
        }}
        self.assertEqual(out, aout)
 
        text = ('RT/4.0 200 ok\n\nid: 10\n\nTicket: 1234567890\n'
            'Type: Create\n\n'
            'Content: First line\n  Second line\n  \n  Third line.\n'
            'Next: aaa\n'
            'Creator: tuser\n'
            'Description: Correspondence added\n'
            'Created: 2013-06-20 06:35:11\n'
        )
        out = self.rt.parse_history_reply(text)
        aout = {'10': {'id': '10',
            'Ticket': '1234567890', 'Type': 'Create',
            'Content': 'First line\nSecond line\n\nThird line.\n',
            'Creator': 'tuser',
            'Description': 'Correspondence added',
            'Created': '2013-06-20 06:35:11',

        }}
        self.assertEqual(out, aout)

        with self.assertRaises(pyrt.BadRequestException):

            text = 'RT/4.0 400 Bad request\n\nReason:\n'
            reply = self.rt.parse_history_reply(text)

        self.assertEqual(out, aout)

    def test_strip_hashes(self):
        
        text = ''
        out = self.rt._strip_hashes(text)
        aout = ''
        self.assertEqual(out, aout)

        text = '#\n#\n#\n#\n'
        out = self.rt._strip_hashes(text)
        aout = ''
        self.assertEqual(out, aout)

        text = 'test\n#\ntest2\n#\n'
        out = self.rt._strip_hashes(text)
        aout = 'test\ntest2\n'
        self.assertEqual(out, aout)


if __name__ == '__main__':

    unittest.main()
