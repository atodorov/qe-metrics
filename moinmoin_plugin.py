#!/usr/bin/python

# Copyright (c) 2012, Alexander Todorov <atodorov@redhat.com>

import os
import getpass
import xmlrpclib
import ConfigParser
from datetime import datetime

def get_config(filename):
    cp = ConfigParser.SafeConfigParser()
    cp.read([filename])

    conf = dict(
            [(key, cp.get('main', key)) for key in [
                'url', 'username'
            ]]
        )

# MoinMoin allows anonymous XML-RPC for the stats
#    try:
#        conf['password'] = cp.get('main', 'password')
#    except ConfigParser.NoOptionError:
#        conf['password'] = getpass.getpass('Password for %s: ' % conf['username'])

    return conf


def get_metrics(start, end, config = None):
    metrics = {}

    if config is None:
        config = get_config(os.environ['HOME'] + '/.qe-metrics/moinmoin.conf')

    user = config['username']
    start_date = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")

    # NB: Plain http
    wiki = xmlrpclib.ServerProxy("http://%s/?action=xmlrpc2" % config['url'])

    # this method can be enhanced
    # http://moinmo.in/FeatureRequests/getRecentChanges_Filters

    changes = wiki.getRecentChanges(start_date)
    count = 0

    for change in changes:
        if change['author'] == user and change['lastModified'] < end_date:
            count += 1

    metrics['edits'] = count

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
        'wiki' : get_metrics(opt.start, opt.end),
    }


    pprint (metrics)
