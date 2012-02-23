#!/usr/bin/python

# Copyright (c) 2012, Alexander Todorov <atodorov@redhat.com>

import os
import sys
import getpass
import xmlrpclib
import kobo.xmlrpc
import ConfigParser

def get_config(filename):
    cp = ConfigParser.SafeConfigParser()
    cp.read([filename])

    conf = dict(
            [(key, cp.get('main', key)) for key in [
                'url', 'username'
            ]]
        )

    try:
        conf['password'] = cp.get('main', 'password')
    except ConfigParser.NoOptionError:
        conf['password'] = getpass.getpass('Password for %s: ' % conf['username'])

    return conf


def get_metrics(start, end, config = None):
    metrics = {}

    if config is None:
        config = get_config(os.environ['HOME'] + '/.qe-metrics/beaker.conf')

    user = config['username']
    password = config['password']

    # cookies are used for authentication
    # Build beaker RPC object
    bkr = xmlrpclib.ServerProxy('https://%s/RPC2' % config['url'], transport=kobo.xmlrpc.retry_request_decorator(kobo.xmlrpc.SafeCookieTransport)())

    # some methods require authentication
    #bkr.auth.login_password(user, password)


    # can't filter jobs by user/period:
    #jobs = bkr.jobs.list('', 1, '', '')


    # new tests and updated tests - N/A

    #bkr.auth.logout()

    return metrics


if __name__ == "__main__":
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
        'beaker' : get_metrics(opt.start, opt.end),
    }

    pprint(metrics)
