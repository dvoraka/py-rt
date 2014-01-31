# -*- coding: utf-8 -*-

'''Module for Request tracker wrapper.'''

from __future__ import unicode_literals
from __future__ import print_function

import requests
import re

####################################
#import ConfigParser
#import codecs
#
#config = ConfigParser.RawConfigParser()
#config.readfp(codecs.open('pyrt.cfg', 'r', 'utf8'))
####################################


class BadRequestException(Exception):
    '''Exception for bad requests.'''
    
    def __init__(self, message):
        
        super(BadRequestException, self).__init__(message)
        self.message = message


class ParseError(Exception):
    '''Error in parsing.'''
    
    def __init__(self, message):
        
        super(ParseError, self).__init__(message)
        self.message = message


class Ticket:
    '''Represent RT ticket.'''

    def __init__(self, id_, subject, data, rt):
        '''Initialize ticket.

        :param id\_: Ticket ID
        :type id\_: str
        :param subject: Ticket subject
        :type subject: str
        :param data: Data
        :type data: {str: str}
        :param rt: RT instance
        :type rt: RT4
        '''
        
        if rt is None:

            raise TypeError('rt cannot be None')

        self.id_ = id_
        self.subject = subject

        self.history = TicketHistory(id_, rt)

        self.due = None
        self.priority = None

        if data:

            self.map_data(data)
        
        self.rt = rt

    def __unicode__(self):
        
        return 'Id: {}, Subject: {}'.format(
            self.id_, self.subject)

    def __str__(self):

        return unicode(self).encode('utf-8')

    def load_all(self):
        '''Load all data.
        
        @rtype: None
        '''
        
        data = self.rt.load_ticket(self.id_)
        self.map_data(data)

        self.load_history()

    def map_data(self, data):
        '''Map data to attributes.

        @type data: {str: str}

        @rtype: None
        '''
        
        self.subject = data.get('Subject', None)

        self.due = data.get('Due', None)
        self.priority = data.get('Priority', None)

    def load_history(self):
        '''Load history.
        
        @rtype: None
        '''
        
        self.history.load()

    def comment(self, text):
        '''Add comment to ticket.
        
        @type text: str
        
        @rtype: None
        '''

        data = {
            'content':
            'Action: correspond\nText: {}\n'.format(text)}
        self.rt.add_comment(self.id_, data)


class TicketHistory:
    '''Store and offer views for history.'''
    
    def __init__(self, id_, rt):
        '''Initialize history.

        :param id\_: ID
        :type id\_: str
        :param rt: RT instance
        :type rt: RT4
        '''
        
        self.id_ = id_
        self.rt = rt

        self.history = None
        self.f_history = None
        self.history_list = None

        self.comments = []

        # wanted history fields
        self.fields = ['Ticket', 'Type', 'Content', 'Creator']
    
    def load(self):
        '''Load all data to object.

        @rtype: None
        '''
        
        data = self.rt.load_history(self.id_)
        self.history = data

#        # filter history to fh
#        fh = {}
#        for history in data:
#
#            fh[history] = self.history_filter(
#                data[history], self.fields)
#

        # for web [{value: content}]
        self.history_list = []
        for hist in sorted(
                self.history,
                key=lambda x: int(x),
                reverse=False):

            self.history_list.append(self.history[hist])

        self.comments = []
        # temporary solution - test
        for comment in sorted(self.history, key=lambda x: int(x)):

            temp = ''
            for key, value in self.history[comment].items():

                temp += key + ': ' + value + '\n'

            self.comments.append(temp)


class TicketList:
    '''Container for tickets.'''

    def __init__(self, data, rt):
        '''Initialize container
        
        @type data: dict of tickets - {str: str}/{'id': 'Subject'}
        '''

        self.tickets = {}
        for id_ in data:

            self.tickets[id_] = Ticket(id_, data[id_], None, rt)

    def list_all(self):
        '''Return tickets info.

        @rtype: tuple of (int, str)
        '''
        
        tinfo = []
        for tid, tobj in self.tickets.items():

            try:

                tinfo.append((int(tid), tobj.subject))

            except ValueError as e:
                
                print(e)

        return tuple(tinfo)

    def __unicode__(self):

        info = 'Ticket list: {} tickets'.format(len(self.tickets))

        return info

    def __str__(self):

        return unicode(self).encode('utf-8')


class RT4:
    '''Request tracker.'''

    def __init__(
            self,
            rest_url='http://localhost/REST/1.0/'):
        '''Initialize RT.

        @type rest_url: str
        '''

        self.rest_url = rest_url
        self.credentials = None
    
    def login(self, login_name, password):
        '''Save credentials.

        @type login: str
        @type password: str

        @rtype: None
        '''
        
        self.credentials = {'user': login_name, 'pass': password}

#    def search(self):
#        '''???'''
#
#        pass

    def check_reply(self, reply):
        '''Check head of reply and return data without head.
        
        @type reply: str

        @rtype: str
        '''

        if not reply:

            return ''

        # create lines from reply
        lines = reply.split('\n')

        code = lines[0]
        code_fields = code.split()

        # simple check
        if code_fields[1] != '200':

            if len(lines) > 2:

                # show first few reply lines
                raise BadRequestException(lines[2:5])

            else:
                
                raise BadRequestException('Unknown error.')

        # create string and remove redundant empty lines at the end
        body = '\n'.join(lines[2:])
        body = body.rstrip() + '\n'

        return body

    def parse_reply(self, reply):
        '''Parse data from string.

        @type reply: str

        @rtype: {str: str}
        '''

        if not reply:

            return None

        lines = self.check_reply(reply).split('\n')

        data = {}
        for line in lines:

            if line == '':
                continue

            if line == 'No matching results.':
                continue

            if line.startswith('#'):
                continue

            fields = line.split(':', 1)
            id_ = fields[0]
            data[id_] = fields[1].lstrip()

        return data

    def parse_history_reply(self, reply):
        '''Parse history data from string.

        @type reply: str

        @rtype: {str: {str: str}}
        '''
        
        if not reply:

            return None

        lines = self.check_reply(reply)

        # {history id: {value: content}}
        history = {}

        contents = lines.split('--')
        for comment in contents:

            h_id = self._history_id(comment)
            values = {}

            # id
            r = re.compile(r'^(id): (\d*)$', re.M)
            found = r.findall(comment)
            if len(found) != 1:

                raise ParseError(len(found))

            v_id = found[0]
            values[v_id[0]] = v_id[1]

            # Ticket
            r = re.compile(r'^(Ticket): (\d*)$', re.M)
            found = r.findall(comment)
            if len(found) != 1:

                raise ParseError(len(found))

            v_ticket = found[0]
            values[v_ticket[0]] = v_ticket[1]

            # Type
            r = re.compile(r'^(Type): (.+)$', re.M)
            found = r.findall(comment)
            if len(found) != 1:

                raise ParseError(len(found))

            v_type = found[0]
            values[v_type[0]] = v_type[1]

            # Content
            r = re.compile(r'^(Content): ((?:.*\n)(?:^ +.*\n)*)', re.M)
            found = r.findall(comment)
            if len(found) > 1:

                raise ParseError(len(found))

            elif found:

                v_content = found[0]
                lines = []
                for line in v_content[1].split('\n'):

                    lines.append(line.lstrip())

                values[v_content[0]] = '\n'.join(lines)

            # Creator
            r = re.compile(r'^(Creator): (.+)$', re.M)
            found = r.findall(comment)
            if len(found) != 1:

                raise ParseError(len(found))

            v_creator = found[0]
            values[v_creator[0]] = v_creator[1]

            # Description
            r = re.compile(r'^(Description): (.+)$', re.M)
            found = r.findall(comment)
            if len(found) != 1:

                raise ParseError(len(found))

            v_description = found[0]
            values[v_description[0]] = v_description[1]

            # Created
            r = re.compile(r'^(Created): (.+)$', re.M)
            found = r.findall(comment)
            if len(found) != 1:

                raise ParseError(len(found))

            v_created = found[0]
            values[v_created[0]] = v_created[1]

            history[h_id] = values

        return history

    def _strip_all(self, history):
        '''Clean history string before next processsing.

        @type history: str

        @rtype: str
        '''

        temp = []
        for line in history.split('\n'):
            if line.startswith('#'):

                continue

            elif line.startswith('\n'):
                
                continue

            else:

                temp.append(line)

        clean_str = '\n'.join(temp)

        new_str = ''
        nl = False
        for char in clean_str:
            
            if char == '\n' and not nl:

                new_str += char
                nl = True
            
            elif char == '\n' and nl:

                nl = True

            else:

                new_str += char
                nl = False

        return new_str

    def _strip_hashes(self, lines):
        '''Delete hashes from start of lines.

        @type lines: str

        @rtype: str
        '''
        
        temp = []
        for line in lines.split('\n'):

            if line.startswith('#'):

                continue

            else:

                temp.append(line)

        return '\n'.join(temp)

    def _history_id(self, history):
        '''Return history id from string.
        
        @type history: str
        
        @rtype: str
        '''

        r = re.compile(r'^id: (\d+)$', re.MULTILINE)

        id_list = r.findall(history)

        if len(id_list) == 1:

            return id_list[0]

        else:

            return None

    def load_ticket(self, id_):
        '''Load ticket data and return it as dictionary.
        
        :param id\_: Ticket ID
        :type id\_: str
        
        :rtype: {str: str}
        '''

        request = requests.get(
            self.rest_url + 'ticket/' + str(id_) + '/show',
            params=self.credentials)

        data = self.parse_reply(request.text)

        return data

    def get_ticket(self, id_):
        '''Return ticket object with data.
        
        :param id\_: Ticket ID
        :type id\_: str

        :rtype: Ticket
        '''

        tdata = self.load_ticket(id_)
        ticket = Ticket(id_, None, tdata, self)

        return ticket

    def search_ticket(self, query):
        '''Search tickets according to query and return TicketList.

        @type query: str

        @rtype: TicketList
        '''

        request = requests.get(
            self.rest_url + 'search/ticket?query=' + query,
            params=self.credentials)

        tl = TicketList(self.parse_reply(request.text), self)

        return tl
    
    def load_history(self, id_):
        '''Load history data for ticket.
        
        :param id\_: Ticket ID
        :type id\_: str
        
        :rtype: {str: {str: str}}
        '''

        request = requests.get(
            self.rest_url + 'ticket/' + id_ + '/history?format=l',
            params=self.credentials)

        history = self.parse_history_reply(request.text)

        # {id: {value: content}}
        return history

    def user_exists(self, username):
        '''Try to find user in RT and return boolean value.

        It depends on 'Disabled' field from RT user reply.

        @type username: str

        @rtype: boolean
        '''

        reply = requests.get(
            self.rest_url + 'user/' + username,
            params=self.credentials)

        print(reply.text)
        data = self.parse_reply(reply.text)

        if 'Disabled' in data:

            return True

        else:

            return False

    def get_usermail(self, username):
        '''Try to find user mail.

        @type username: str

        @rtype: str
        '''

        reply = requests.get(
            self.rest_url + 'user/' + username,
            params=self.credentials)

        data = self.parse_reply(reply.text)

        if __debug__:
            print('get_usermail data:\n{}'.format(data))

        mail = data['EmailAddress']

        return mail

#    def history(self, id_):
#        '''???'''
#
#        request = requests.get(
#            self.rest_url + 'ticket/' + id_ + '/history?format=l',
#            params=self.credentials)
#
#        return request.text
#
    def add_comment(self, id_, message):
        '''Add comment to ticket.
        
        :param id\_: Ticket ID
        :type id\_: str
        :param message: Comment text
        :type message: str

        :rtype: None
        '''

        payload = message
        reply = requests.post(
            self.rest_url + 'ticket/' + id_ + '/comment',
            params=self.credentials, data=payload)
        if __debug__:
            print('add_comment reply:\n{}'.format(reply.text))

    def create_ticket(self, ticket_data):
        '''Create ticket and return info.
        
        @type ticket_data: dict - {'content': ticket body}
        
        @rtype: str
        '''

        payload = ticket_data
        reply = requests.post(
            self.rest_url + 'ticket/new',
            params=self.credentials, data=payload)
        if __debug__:
            print('create_ticket reply:\n{}'.format(reply.text))

        info = self.check_reply(reply.text)

        return info


class RequestTracker:
    'High-level API for RT'
    
    pass
