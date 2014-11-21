#!/usr/bin/python

# Copyright (c) 2012, Alexander Todorov <atodorov@redhat.com>

import os
from nitrate_driver import NitrateXmlrpc

def get_metrics(start, end, author = None):
    metrics = {}

    if author:
        print "Nitrate plugin do not support --author option!"

    nitrate = NitrateXmlrpc.from_config(os.environ['HOME'] + '/.qe-metrics/nitrate.conf')
    user = nitrate.get_me()


    ##### Test Plans created during period
    plans = nitrate.server.TestPlan.filter_count(
                            {
                                'author' : user['id'],
                                'create_date__gte' : start, 
                                'create_date__lte' : end,
                            }
                        )

    metrics['plans'] = plans

    ##### Test Cases created during period

    cases = nitrate.server.TestCase.filter_count(
                            {
                                'author' : user['id'],
                                'create_date__gte' : start, 
                                'create_date__lte' : end,
                            }
                        )

    metrics['cases'] = cases

    ##### Test Runs executed during period

    runs = nitrate.server.TestRun.filter_count(
                            {
                                'manager' : user['id'],
                                'stop_date__gte' : start,
                                'stop_date__lte' : end,
                            }
                        )

    metrics['runs'] = runs

    ##### Test Case Run execution during period

    caseruns = nitrate.server.TestCaseRun.filter_count(
                            {
                                'tested_by' : user['id'],
                                'close_date__gte' : start,
                                'close_date__lte' : end,
                            }
                        )

    metrics['case_runs'] = caseruns


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
        'nitrate' : get_metrics(opt.start, opt.end),
    }

    pprint(metrics)
