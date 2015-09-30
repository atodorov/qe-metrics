#!/usr/bin/env python

# Copyright (c) 2015, Alexander Todorov <atodorov@redhat.com>

import os
import sys
import ConfigParser
from utils import load_json
from datetime import datetime

def get_config(filename):
    cp = ConfigParser.SafeConfigParser()
    cp.read([filename])

    conf = dict(
            [(key, cp.get('main', key)) for key in [
                'username'
            ]]
        )

    return conf

def get_metrics(start, end, author = None, config = None):

    # GitHub search API uses dates, not hours
    if len(start) == 19:
        start = start[:-9]
        end = end[:-9]

    metrics = {}

    if config is None:
        config = get_config(os.environ['HOME'] + '/.qe-metrics/github.conf')

    user = config['username']

    if not author:
        author = user

    ##### NEW issues opened during period
    url = 'https://api.github.com/search/issues?q=author:%s+created:%s..%s' % \
            (author, start, end)
    result = load_json(url)

    prs = 0 # pull requests
    for item in result['items']:
        if item.has_key('pull_request'):
            prs += 1
    metrics['issues'] = int(result['total_count']) - prs
    metrics['pull_requests'] = prs

    #### get all events in the last 90 days and filter out commits
    result = load_json('https://api.github.com/users/%s/events/public' % author)
    commits = 0
    start_dt = datetime.strptime(start, '%Y-%m-%d')
    end_dt = datetime.strptime(end + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

    for event in result:
        if event['type'] == "PushEvent":
            created_at = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            if start_dt <= created_at <= end_dt:
                commits += event['payload']['size']
    metrics['commits'] = commits

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

# GitHub search API uses dates, not hours
#    opt.start = '%s 00:00:00' % opt.start
#    opt.end = '%s 23:59:59' % opt.end

    metrics =  {
        'start' : opt.start,
        'end'   : opt.end,
        'github' : get_metrics(opt.start, opt.end, opt.author),
    }

    pprint(metrics)
