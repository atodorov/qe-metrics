#!/usr/bin/python

# Copyright (c) 2012, Alexander Todorov <atodorov@redhat.com>

import os
import sys
import getpass
import bugzilla
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

def get_metrics(start, end, author = None, config = None):
    metrics = {}

    if config is None:
        config = get_config(os.environ['HOME'] + '/.qe-metrics/bugzilla.conf')

    user = config['username']
    password = config['password']

    if not author:
        author = user

    bz = bugzilla.Bugzilla(url='https://%s/xmlrpc.cgi' % config['url'])
    if not bz.login(user, password):
        print 'Login failed.'
        sys.exit(1)

    ##### NEW bugs opened during period
    qd = {
        'query_format' : 'advanced',

        'reporter' : author,
        'chfieldfrom' : start,
        'chfieldto' : end,
        'chfield' : '[Bug creation]',
    }

    bugs = bz.query(qd)

    metrics['opened'] = len(bugs)
    #metrics['opened_ids'] = [b.id for b in bugs]


    ##### Bugs VERIFIED during period

    qd = {
        'query_format' : 'advanced',
        'j_top' : 'AND_G',

        'f1' : 'bug_status',
        'o1' : 'changedto',
        'v1' : 'VERIFIED',

        'f2' : 'bug_status',
        'o2' : 'changedby',
        'v2' : author,

        'f3' : 'bug_status',
        'o3' : 'changedafter',
        'v3' : start,

        'f4' : 'bug_status',
        'o4' : 'changedbefore',
        'v4' : end,
    }

    bugs = bz.query(qd)

    metrics['verified'] = len(bugs)
    #metrics['verified_ids'] = [b.id for b in bugs]

    ##### Bugs VERIFIED SanityOnly during period

    qd = {
        'query_format' : 'advanced',
        'j_top' : 'AND_G',

        'f1' : 'cf_verified',
        'o1' : 'substring',
        'v1' : 'SanityOnly',

        'f2' : 'cf_verified',
        'o2' : 'changedby',
        'v2' : author,

        'f3' : 'cf_verified',
        'o3' : 'changedafter',
        'v3' : start,

        'f4' : 'cf_verified',
        'o4' : 'changedbefore',
        'v4' : end,
    }

    bugs = bz.query(qd)

    metrics['verified_sanity_only'] = len(bugs)
    #metrics['verified_sanity_only_ids'] = [b.id for b in bugs]


    ##### Bugs moved back to ASSIGNED during period

    qd = {
        'query_format' : 'advanced',
        'j_top' : 'AND_G',

        'f1' : 'bug_status',
        'o1' : 'changedto',
        'v1' : 'ASSIGNED',

        'f2' : 'bug_status',
        'o2' : 'changedby',
        'v2' : author,

        'f3' : 'bug_status',
        'o3' : 'changedafter',
        'v3' : start,

        'f4' : 'bug_status',
        'o4' : 'changedbefore',
        'v4' : end,
    }

    bugs = bz.query(qd)

    metrics['assigned'] = len(bugs)
    #metrics['assigned_ids'] = [b.id for b in bugs]


    ##### Bugs qa_ack+ during period

    qd = {
        'query_format' : 'advanced',

        'f1' : 'setters.login_name',
        'o1' : 'equals',
        'v1' : author,

        'f2' : 'flagtypes.name',
        'o2' : 'changedto',
        'v2' : 'qa_ack+',

        'f3' : 'flagtypes.name',
        'o3' : 'changedafter',
        'v3' : start,

        'f4' : 'flagtypes.name',
        'o4' : 'changedbefore',
        'v4' : end,
    }

    bugs = bz.query(qd)

    metrics['qa_ack+'] = len(bugs)
    #metrics['qa-ack+_ids'] = [b.id for b in bugs]

    return metrics


if __name__ == "__main__":
    import os
    import optparse
    from pprint import pprint

    p = optparse.OptionParser()
    p.add_option('-s', '--start',  dest="start",  default=None, help="Start date: YYYY-MM-DD")
    p.add_option('-e', '--end',    dest="end",    default=None, help="End date:   YYYY-MM-DD")
    p.add_option('-a', '--author', dest="author", default=None, help="Author of the action. Defaults to yourself.")

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
        'bugzilla' : get_metrics(opt.start, opt.end, opt.author),
    }

    pprint(metrics)
