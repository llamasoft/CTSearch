import time
import requests
import json
import itertools
import logging
import tld
import threading
from collections import namedtuple


SearchResponse = namedtuple("SearchResponse", [
    "type",
    "results",
    "filters",
    "paging"
])

SearchResult = namedtuple("SearchResult", [
    "cert_serial",
    "subject",
    "issuer",
    "valid_from",
    "valid_to",
    "cert_hash",
    "ct_log_count",
    "first_entry",
    "dns_count"
])

SearchFilters = namedtuple("SearchFilters", [
    "issuer_uid",
    "issuer_hash",
    "issuer_name",
    "issuer_count"
])

SearchPaging = namedtuple("SearchPaging", [
    "prev_hash",
    "next_hash",
    "unknown",
    "page_num",
    "page_count"
])


# The response we get back from the API
CertResponse = namedtuple("CertResponse", [
    "type",     # 'https.ct.chr'
    "result",   # CertResult
    "logs"      # CertLog
])

# The actual certificate info that contains our search domain
CertResult = namedtuple("CertResult", [
    "cert_serial",
    "subject",
    "issuer",
    "valid_from",
    "valid_to",
    "cert_type",
    "hash_type",
    "domains"
])

# The Certificate Transparency log sources that contain the CertResult
CertLog = namedtuple("CertLog", [
    "name",
    "hash",
    "index"
])



class CTSearch(object):
    API_ROOT = "https://transparencyreport.google.com/transparencyreport/api/v3"
    SEARCH_API = "/httpsreport/ct/certsearch"
    PAGING_API = "/httpsreport/ct/certsearch/page"  # p=page_hash
    BYHASH_API = "/httpsreport/ct/certbyhash"       # hash=cert_hash


    def __init__(self):
        self.last_request = 0
        self.logger = logging.getLogger("CTSearch")


    def _parse_api_response(self, response):
        # Google's API responses always start a "magic line" to prevent XXS via API abuse
        # Typically this is )]}', but to play it safe, we remove the entire first line
        magic, newline, content = response.content.partition("\n")
        return json.loads(content)[0]


    def _api_call(self, endpoint, api_params):
        response = requests.get(self.API_ROOT + endpoint, params = api_params)
        return self._parse_api_response(response)


    def _parse_search_response(self, json_response):
        type, results, filters, paging = json_response
        # Sometimes there are certificates that somehow have no domain names
        # They lack a ct_log_count or dns_count value which causes the list size to be wrong
        results = [SearchResult(*r) for r in results if len(r) == 9]
        filters = [SearchFilters(*f) for f in filters]
        paging  = SearchPaging(*paging)
        return SearchResponse(type, results, filters, paging)


    def _parse_cert_response(self, json_response):
        type, result, logs = json_response
        result   = CertResult(*result)
        log_list = [CertLog(*l) for l in logs]
        log_dict = {l.name: l.index for l in log_list}
        return CertResponse(type, result, log_dict)


    def _search(self, domain, include_expired = True):
        """Fetches the first page of search results for `domain`."""
        self.logger.info("Searching for domain: {}".format(domain))
        api_params = {
            "domain": domain,
            "include_subdomains": "true",
            "include_expired": "true" if include_expired else "false",
        }
        json_response = self._api_call(self.SEARCH_API, api_params)
        return self._parse_search_response(json_response)


    def _search_page(self, page_hash):
        """Fetches a search result page by hash."""
        self.logger.debug("Fething result page by hash: {}".format(page_hash))
        api_params = {
            "p": page_hash,
        }
        json_response = self._api_call(self.PAGING_API, api_params)
        return self._parse_search_response(json_response)


    def _cert(self, cert_hash):
        """Fetches a certificate's info by hash."""
        self.logger.debug("Fetching certificate by hash: {}".format(cert_hash))
        api_params = {"hash": cert_hash}
        json_response = self._api_call(self.BYHASH_API, api_params)
        return self._parse_cert_response(json_response)


    def search(self, search_domain, include_expired = True, page_limit = 25):
        """Returns all unique subdomains for `search_domain` by searching Certificate Transparency logs."""
        search_domain = search_domain.lower()
        all_domains = {}
        next_page_hash = None


        def fetch_cert(cert_hash, search_domain, result_dict):
            """Fetches a certificate by hash and adds it to `result_dict` if it hasn't been seen before."""
            cert_response = self._cert(cert_hash)

            for cert_domain in cert_response.result.domains:
                cert_domain = cert_domain.lower()
                parsed_domain = tld.get_tld(
                    cert_domain,
                    as_object     = True,
                    fail_silently = True,
                    fix_protocol  = True
                )
                if not parsed_domain:
                    continue

                if parsed_domain.tld.lower() != search_domain.lower():
                    continue

                if cert_domain not in result_dict:
                    self.logger.debug("Adding new subdomain: {}".format(cert_domain))
                    result_dict[cert_domain] = cert_response


        for page_num in itertools.count(1):
            if page_num == 1:
                page_response = self._search(search_domain, include_expired = include_expired)
            elif next_page_hash is not None and page_num <= page_limit:
                page_response = self._search_page(next_page_hash)
            elif page_num > page_limit:
                self.logger.info("Search page limit reached")
                break
            else:
                # Generic end of search results (next_page_hash is None)
                break

            self.logger.info(
                "Fetching certificates for page {} of {}".format(
                    page_num,
                    page_response.paging.page_count
                )
            )

            cert_threads = []
            for result in page_response.results:
                cert_thread = threading.Thread(
                    target = fetch_cert,
                    args = (result.cert_hash, search_domain, all_domains)
                )
                cert_thread.daemon = True
                cert_thread.start()
                cert_threads.append(cert_thread)

            for thread in cert_threads:
                thread.join()

            next_page_hash = page_response.paging.next_hash

        return all_domains
