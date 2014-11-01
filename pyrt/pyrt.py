# -*- coding: utf-8 -*-

'''Module for Request tracker wrapper.'''

from __future__ import unicode_literals
from __future__ import print_function

import requests
import re

__all__ = [
    'BadRequestException',
    'ParseError',
    'Ticket',
    'TicketHistory',
    'TicketList',
    'RT4'
]


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
    '''Represent RT ticket.

    :param str id\_: Ticket ID
    :param str subject: Ticket subject
    :param str data: Data
    :param RT4 rt: RT instance
    :raise TypeError: If rt is None

    '''

    def __init__(self, id_, subject, data, rt):
        '''Initialize ticket.'''

        if rt is None:

            raise TypeError('rt cannot be None')

        self.id_ = id_
        self.subject = subject

        self.history = TicketHistory(id_, rt)

        self.creator = None
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

        :return: None
        '''

        data = self.rt.load_ticket(self.id_)
        self.map_data(data)

        self.load_history()

    def map_data(self, data):
        '''Map data to attributes.

        :param data: Data
        :type data: {str: str}

        :return: None
        '''

        self.subject = data.get('Subject', None)

        self.creator = data.get('Creator', '')
        self.due = data.get('Due', None)
        self.priority = data.get('Priority', None)

    def load_history(self):
        '''Load history.

        :return: None
        '''

        self.history.load()

    def comment(self, text):
        '''Add comment to ticket.

        :param str text: Text

        :return: None
        '''

        data = {
            'content':
            'Action: correspond\nText: {}\n'.format(text)}
        self.rt.add_comment(self.id_, data)


class TicketHistory:
    '''Store and offer views for history.

    :param id\_: ID
    :type id\_: str
    :param rt: RT4 instance
    :type rt: :class:`RT4`
    '''

    def __init__(self, id_, rt):
        '''Initialize history.'''

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

        :return: None
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
    '''Container for tickets.

        :param data: Tickets
        :type data: dict of tickets {str: str}/{'id': 'Subject'}
        '''

    def __init__(self, data, rt):
        '''Initialize container'''

        self.tickets = {}

        if data is not None:

            for id_ in data:

                self.tickets[id_] = Ticket(id_, data[id_], None, rt)

    def list_all(self):
        '''Return tickets info.

        :return: tuple of (int, str)
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
    '''Request tracker.

    :param str rest_url: REST URL
    '''

    def __init__(
            self,
            rest_url='http://localhost/REST/1.0/'):
        '''Initialize RT.'''

        self.rest_url = rest_url
        self.credentials = None

    def login(self, login_name, password):
        '''Save credentials.

        :param str login_name: Login
        :param str password: Password

        :return: None
        '''

        self.credentials = {'user': login_name, 'pass': password}

    def check_reply(self, reply):
        '''Check head of reply and return data without head.

        :param str reply: Reply text
        :raise BadRequestException: If reply from RT is not OK

        :return: str
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

        :param str reply: Reply text

        :return: {str: str}
        '''

        if not reply:

            return None

        try:

            lines = self.check_reply(reply).split('\n')

        except BadRequestException as e:

            print(e)
            return None

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

        :param str reply: History reply text

        :return: {str: {str: str}}
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

        :param str history: History text

        return: str
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

        :param str lines: Lines string

        :return: str
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

        :param str history: History text

        :return: str
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

        :param str query: Query

        :return: :class:`TicketList`
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

        :param str username: Username

        :return: bool
        '''

        reply = requests.get(
            self.rest_url + 'user/' + username,
            params=self.credentials)

        # print(reply.text)
        data = self.parse_reply(reply.text)

        if 'Disabled' in data:

            return True

        else:

            return False

    def create_user(self, user_data):
        '''Create user.

        :param user_data: User raw data
        :type user_data: dict - {'content': user data}

        :return: str
        '''

        payload = user_data
        reply = requests.post(
            self.rest_url + 'user/new',
            params=self.credentials, data=payload)

        info = self.check_reply(reply.text)

        return info

    def create_group(self, group_data):
        '''Create group.

        :param group_data: Group raw data
        :type group_data: dict - {'content': group data}

        :return: str
        '''

        payload = group_data
        reply = requests.post(
            self.rest_url + 'group/new',
            params=self.credentials, data=payload)

        info = self.check_reply(reply.text)

        return info

    def edit_group(self, groupname, group_data):
        '''Edit group - limited.

        :return: str
        '''

        payload = group_data
        reply = requests.post(
            self.rest_url + 'group/' + groupname + '/edit',
            params=self.credentials, data=payload)

        info = reply.text  # self.check_reply(reply.text)

        return info

    def get_usermail(self, username):
        '''Try to find user's mail.

        :param str username: Username

        :return: str
        '''

        reply = requests.get(
            self.rest_url + 'user/' + username,
            params=self.credentials)

        data = self.parse_reply(reply.text)

        # if __debug__:
        #    print('get_usermail data:\n{}'.format(data))

        if data is not None:

            mail = data.get('EmailAddress', '')

        else:

            mail = ''

        return mail

    def get_userlang(self, username):
        '''Return user's language.

        :param str username: Username

        :return: str
        '''

        reply = requests.get(
            self.rest_url + 'user/' + username,
            params=self.credentials)

        data = self.parse_reply(reply.text)

        # if __debug__:
        #    print('get_userlang data:\n{}'.format(data))

        if data is not None:

            lang = data.get('Lang', '').lower()

        else:

            lang = ''

        return lang

    def set_userlang(self, username, user_data):
        '''Edit user's language. Need root user.

        :param str username: Username

        :return: str
        '''

        payload = user_data
        reply = requests.post(
            self.rest_url + 'user/' + username + '/edit',
            params=self.credentials, data=payload)

        info = self.check_reply(reply.text)

        return info

    def add_comment(self, id_, message):
        '''Add comment to ticket.

        :param id\_: Ticket ID
        :type id\_: str
        :param message: Comment text
        :type message: str

        :rtype: None
        '''

        payload = message
        # TODO: add logging for the reply
        requests.post(
            self.rest_url + 'ticket/' + id_ + '/comment',
            params=self.credentials, data=payload)
        # if __debug__:
        #    print('add_comment reply:\n{}'.format(reply.text))

    def create_ticket(self, ticket_data):
        '''Create ticket and return info.

        :param ticket_data: Ticket data
        :type ticket_data: dict - {'content': ticket body}

        :return: str
        '''

        payload = ticket_data
        reply = requests.post(
            self.rest_url + 'ticket/new',
            params=self.credentials, data=payload)
        # if __debug__:
        #    print('create_ticket reply:\n{}'.format(reply.text))

        try:

            info = self.check_reply(reply.text)

        except BadRequestException as e:

            print(e)
            return 'Cannot create ticket.'

        return info


class RequestTracker:
    'High-level API for RT'

    pass
