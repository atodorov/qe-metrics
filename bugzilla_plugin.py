#!/usr/bin/python

# Copyright (c) 2012, Alexander Todorov <atodorov@redhat.com>

import os
import sys
import time
import getpass
import bugzilla
import requests
import ConfigParser
from bugzilla.base import BugzillaError

def bugzilla_query(bz, query, config):
    """
        Retry Bugzilla queries in case of proxy error.

        Note: constructor of bugzilla.Bugzilla class will return appropriate
        class based on URL which breaks my attempts to override this class and
        provide a cleaner interface!
    """
    max_retries = config.get('max_retries', 10)
    retry_sleep = config.get('retry_sleep', 10) # seconds
    attempt = 0

    while True:
        try:
            attempt += 1
            return bz.query(query)
        except requests.exceptions.HTTPError as e:
            if (e.response.status_code == 502) and (e.response.reason == 'Proxy Error'):
                # This exception is safe to ignore.
                # If there is another similar exception, it can be added here.

                if attempt >= max_retries:
                    raise Exception("We're unable to perform Bugzilla query due to 'Proxy Error'. Probably Bugzilla server have some difficulties.")
                else:
                    print "INFO: Unabe to execute query due to: '%s: %s'. Trying again (attempt %s out of %s)." % \
                        (sys.exc_info()[0], sys.exc_info()[1], attempt+1, max_retries)
                    time.sleep(retry_sleep)
            else:
                # It is safer not to ignore all other exceptions
                raise


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

    while True:
        try:
            bz.login(user, password)
            break
        except BugzillaError, e:
            if e.message.find('Login failed') > -1:
                password = getpass.getpass('Password for %s: ' % user)
                continue
            else:
                print e.message
                sys.exit(1)

    ##### NEW bugs opened during period
    qd = {
        'query_format' : 'advanced',

        'reporter' : author,
        'chfieldfrom' : start,
        'chfieldto' : end,
        'chfield' : '[Bug creation]',
    }

    bugs = bugzilla_query(bz, qd, config)

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

    bugs = bugzilla_query(bz, qd, config)

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

    bugs = bugzilla_query(bz, qd, config)

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

    bugs = bugzilla_query(bz, qd, config)

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

    bugs = bugzilla_query(bz, qd, config)

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
