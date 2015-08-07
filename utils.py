#!/usr/bin/env python

# Copyright (c) 2015, Alexander Todorov <atodorov@redhat.com>

import json
import httplib

def fetch_url(url):
    (proto, host_path) = url.split('//')
    (host_port, path) = host_path.split('/', 1)
    path = '/' + path

    if url.startswith('https'):
        conn = httplib.HTTPSConnection(host_port)
    else:
        conn = httplib.HTTPConnection(host_port)

    # GitHub requires a valid UA string
    headers = {
        'User-Agent' : 'qe-metrics / https://github.com/atodorov/qe-metrics',
    }

    conn.request("GET", path, headers=headers)
    response = conn.getresponse()

    if (response.status == 404):
        raise Exception("404 - %s not found" % url)

    if response.status in [301, 302]:
        location = response.getheader('Location')
        return fetch_page(location)

    return response.read().decode('UTF-8', 'replace')

def load_json(url):
    data = fetch_url(url)
    return json.loads(data)

