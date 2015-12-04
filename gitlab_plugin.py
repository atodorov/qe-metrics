#!/usr/bin/env python

# Copyright (c) 2015, Alexander Todorov <atodorov@redhat.com>

import os
import sys
import ConfigParser
from utils import fetch_url
from datetime import datetime
from xml.dom.minidom import parseString

def get_config(filename):
    cp = ConfigParser.SafeConfigParser()
    cp.read([filename])

    conf = dict(
            [(key, cp.get('main', key)) for key in [
                'username', 'url', 'private_token'
            ]]
        )

    return conf

def get_metrics(start, end, author = None, config = None):
    start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")

    metrics = {
        'commits' : 0,
        'git_push' : 0,
        'issues' : {
            'opened' : 0,
            'closed' : 0,
        },
        'merge_requests' : {
            'opened' : 0,
            'closed' : 0,
        },
    }

    if config is None:
        config = get_config(os.environ['HOME'] + '/.qe-metrics/gitlab.conf')

    url = config['url']
    user = config['username']
    token = config['private_token']

    if not author:
        author = user

    ##### NEW issues opened during period
    atom_url = '%s/u/%s.atom?private_token=%s' % (url, author, token)
    dom = parseString(fetch_url(atom_url))

    for entry in dom.getElementsByTagName("entry"):
        title = entry.getElementsByTagName("title")[0].firstChild.wholeText
        updated_on = entry.getElementsByTagName("updated")[0].firstChild.wholeText
        updated_on = datetime.strptime(updated_on, "%Y-%m-%dT%H:%M:%SZ")

        # skip older or newer events
        if not (start <= updated_on <= end):
            continue

        if title.find('pushed') > -1:
            metrics['git_push'] += 1

            # commits is a bit wrong.
            # when pushing to a new branch for the first time
            # GitLab reports commits from other users as well,
            # for example when merging to the latest upstream
            # this can be fixed by a second parameter, the user real name
            # as it appears in the commits, but it doesn't work
            # nicely with --author and isn't that important for now!
            for summary in entry.getElementsByTagName("summary"):
                for a in summary.getElementsByTagName("a"):
                    href = a.getAttribute('href')
                    if href.find('/commit/') > -1:
                        metrics['commits'] += 1
        elif title.find('opened issue') > -1:
            metrics['issues']['opened'] += 1
        elif title.find('closed issue') > -1:
            metrics['issues']['closed'] += 1
        elif title.find('opened MR') > -1:
            metrics['merge_requests']['opened'] += 1
        elif title.find('accepted MR') > -1:
            metrics['merge_requests']['closed'] += 1



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
        'gitlab' : get_metrics(opt.start, opt.end, opt.author),
    }

    pprint(metrics)
