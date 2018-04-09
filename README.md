CTSearch
==========

A Certificate Transparency search utility and usable demo.

Results are gathered from Google's [Transparency Report](https://transparencyreport.google.com/https/certificates) using an undocumented API.
Because of this, the library and demo may break or cease working at any moment.


Demo
------

All options:

    $ python search_demo.py --help
    usage: search_demo.py [-h] [-l LIMIT] [-e] domain

    positional arguments:
      domain                Domain that you want to search for subdomains

    optional arguments:
      -h, --help            show this help message and exit
      -l LIMIT, --limit LIMIT
                            Maximum number of result pages to scan
      -e, --expired         Include results from expired certificates

Basic usage:

    $ python search_demo.py spotify.com
    [2018-04-09 13:46:14,362][CTSearch][INFO] Searching for domain: spotify.com
    [2018-04-09 13:46:14,911][CTSearch][INFO] Fetching certificates for page 1 of 5
    [2018-04-09 13:46:18,427][CTSearch][INFO] Fetching certificates for page 2 of 5
    [2018-04-09 13:46:21,890][CTSearch][INFO] Fetching certificates for page 3 of 5
    [2018-04-09 13:46:24,952][CTSearch][INFO] Fetching certificates for page 4 of 5
    [2018-04-09 13:46:28,356][CTSearch][INFO] Fetching certificates for page 5 of 5
    [2018-04-09 13:46:29,371][Main][INFO] Found 35 subdomains
    [2018-04-09 13:46:29,371][Main][INFO] Found subdomain: wg.spotify.com
    [2018-04-09 13:46:29,371][Main][INFO]    Cert Subject: C=SE, O=Spotify AB, L=Stockholm, CN=*.wg.spotify.com
    [2018-04-09 13:46:29,371][Main][INFO]    Cert Domains: [u'*.wg.spotify.com', u'wg.spotify.com']
    [2018-04-09 13:46:29,371][Main][INFO] Found subdomain: pay.spotify.com
    [2018-04-09 13:46:29,372][Main][INFO]    Cert Subject: C=SE, O=Spotify AB, L=Stockholm, ST=Stockholm, CN=pay.spotify.com
    [2018-04-09 13:46:29,372][Main][INFO]    Cert Domains: [u'pay.spotify.com']
    ...
