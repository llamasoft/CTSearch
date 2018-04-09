from CTSearch import CTSearch
import logging
import json
import argparse


# These sources will result in a lot of extra noise if not silenced
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

logging.basicConfig(
    format = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
    level = logging.INFO
)
logger = logging.getLogger("Main")


parser = argparse.ArgumentParser()
parser.add_argument(
    "domain",
    help = "Domain that you want to search for subdomains"
)
parser.add_argument(
    "-l", "--limit",
    help = "Maximum number of result pages to scan",
    type = int,
    default = 10
)
parser.add_argument(
    "-e", "--expired",
    help = "Include results from expired certificates",
    action = "store_true"
)
parser.parse_args()
args = parser.parse_args()


searcher = CTSearch()
subdomains = searcher.search(
    args.domain,
    page_limit = args.limit,
    include_expired = args.expired
)
logger.info("Found {} subdomains".format(len(subdomains)))
for subdomain, response in subdomains.iteritems():
    # `response` is a CertResponse (raw API response) with members:
    #   `result` - CertResult, the actual certificate
    #   `logs`   - CertLog, where and in which CT sources the certificate is found
    # For object structures and all of their members, see `CTSearch.py`
    logger.info("Found subdomain: {}".format(subdomain))
    logger.info("   Cert Subject: {}".format(response.result.subject))
    logger.info("   Cert Domains: {}".format(response.result.domains))
