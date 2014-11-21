#!/usr/bin/python

# Copyright (c) 2012, Alexander Todorov <atodorov@redhat.com>

import os
import pycurl
import urllib
import getpass
import ConfigParser

def get_config(filename):
    cp = ConfigParser.SafeConfigParser()
    cp.read([filename])

    conf = dict(
            [(key, cp.get('main', key)) for key in [
                'url', 'email'
            ]]
        )

    conf['krb_auth'] = cp.get('main', 'krb_auth')

    if not conf['krb_auth']:
        try:
            conf['password'] = cp.get('main', 'password')
        except ConfigParser.NoOptionError:
            conf['password'] = getpass.getpass('Password for %s: ' % conf['username'])

    return conf


class Response:
    def __init__(self):
        self.reset()

    def write_content(self, buf):
        self.contents = self.contents + buf

    def reset(self):
        self.contents = ''


def get_metrics(start, end, author = None, config = None):
    metrics = {}

    if author:
        print "Request Tracker plugin do not support --author option!"

    if config is None:
        config = get_config(os.environ['HOME'] + '/.qe-metrics/request_tracker.conf')

    user = config['email']

    # here is the RequestTracker URI we try to access
    base_uri = 'https://%s/REST/1.0/' % config['url']


    # setup curl
    response = Response()
    c = pycurl.Curl()
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.WRITEFUNCTION, response.write_content)
    c.setopt(pycurl.SSL_VERIFYPEER, 0)

    if config['krb_auth']:
        c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_GSSNEGOTIATE)
        c.setopt(pycurl.USERPWD, '%s:foo' % user)
    else:
        password = config['password']
        c.setopt(pycurl.USERPWD, '%s:%s' % (user, password))



    # Tickets created during period:
    url = base_uri + "/search/ticket?format=i&query=" + urllib.quote("Creator='%s' AND Created > '%s' AND Created < '%s'" % (user, start, end))
    c.setopt(pycurl.URL, str(url))
    c.perform()

    tickets = response.contents.decode('UTF-8')
    response.reset()
    tickets = [t for t in tickets.split("\n") if t.startswith('ticket')]
    metrics['opened'] = len(tickets)


    # Tickets assigned to user and Resolved during period:
    url = base_uri + "/search/ticket?format=i&query=" + urllib.quote("Owner='%s' AND Resolved > '%s' AND Resolved < '%s'" % (user, start, end))
    c.setopt(pycurl.URL, str(url))
    c.perform()

    tickets = response.contents.decode('UTF-8')
    response.reset()
    tickets = [t for t in tickets.split("\n") if t.startswith('ticket')]
    metrics['resolved'] = len(tickets)

#todo: number of comments on tickets (where user is not owner/assignee)


    c.close()

    return metrics


if __name__ == "__main__":
    import sys
    import optparse
    from pprint import pprint

    p = optparse.OptionParser()
    p.add_option('-s', '--start', dest="start", default=None, help="Start date: YYYY-MM-DD")
    p.add_option('-e', '--end',   dest="end",   default=None, help="End date:   YYYY-MM-DD")

    (opt, args) = p.parse_args()

    if not opt.start:
        print "--start is mandatory!"
        sys.exit(1)

    if not opt.end:
        print "--end is mandatory!"
        sys.exit(1)

    opt.start = '%s 00:00:00' % opt.start
    opt.end = '%s 23:59:59' % opt.end

    metrics =  {
        'start' : opt.start,
        'end'   : opt.end,
        'rt' : get_metrics(opt.start, opt.end),
    }

    pprint(metrics)
