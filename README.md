QE-Metrics is a set of tools which provide metrics information for QE folks.

It's goal is to make it easy to track personal performance for people working
in QE departments. The project has a modular architecture to allow extracting
metrics from different QE related systems.

Installation
-------------

        git clone git://github.com/atodorov/qe-metrics.git

Configuration
-------------

Create config files in `~/.qe-metrics`:

* `qe-metrics.conf`

        # Set to 0 to disable
        [plugins]
        beaker = 1
        bugzilla = 1
        github = 1
        moinmoin = 1
        nitrate = 1
        request_tracker = 1

* `beaker.conf`

        [main]
        url = beaker.example.com
        username = you@example.com

* `bugzilla.conf`
   (requires installing the python-bugzilla package)

        [main]
        url = bugzilla.example.com
        username = you@example.com

* `github.conf`

        [main]
        username = your_username

* `moinmoin.conf`

        [main]
        url = wiki.example.com
        username = you

* `nitrate.conf`

        [nitrate]
        url = https://nitrate.example.com/xmlrpc/
        username = you@example.com
        password = foo
        use_mod_kerb = True

* `request_tracker.conf`

        [main]
        url = rt.example.com/rt
        email = you@example.com
        krb_auth = True




QE-Metrics will ask for password when needed if not specified. 
It prefers using Kerberos auth if this is supported.

Execution
---------

        ./qe-metrics --start 2012-02-01 --end 2012-02-29

Metrics
-------

* [Beaker](http://fedorahosted.org/beaker) - automated testing framework
    - **NOT YET IMPLEMENTED**
    - number of new/updated tests
    - number of test jobs execution
* [Bugzilla](http://www.bugzilla.org/) - bug tracking
    - number of bugs where status changed to `ASSIGNED`
    - number of newly opened bugs
    - number of bugs where status changed to `VERIFIED`
    - If Flags and additional fields are available
        * number of bug where flag was set to `qa_ack+`
        * number of bugs were cf_verified field was set to SanityOnly
* [GitHub](https://github.com) - code collaboration
    - number of newly opened issues
    - number of newly opened pull requests
    - number of commits across any public repositories
* [GitLab](https://gitlab.com) - code collaboration
    - number of opened and closed issues
    - number of opened and closed merge requests
    - number of commits and git push actions
* [MoinMoin](http://moinmo.in) - collaborative wiki
    - number of edits
* [Nitrate](http://fedorahosted.org/nitrate) - test case management
    - number of created test plans
    - number of created test cases
    - number of test runs executed
    - total number of test cases executed
* [Request Tracker](http://bestpractical.com/rt/) - issues tracker
    - number of newly opened tickets
    - number of resolved tickets
