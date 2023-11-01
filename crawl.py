import concurrent.futures
import json
import socket
import threading
import time
from collections import defaultdict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import ignored_extensions, programming_languages


def _count_language_mentions(text):
    mention_count = defaultdict(int)
    for token in text.split(" "):
        if token in programming_languages:
            mention_count[token] += 1

    return mention_count


def _crawl_url(response):
    doc = BeautifulSoup(response.content, features="lxml")
    parsed_parent_url = urlparse(response.url)

    next_urls = set()

    for link in doc.find_all(href=True):
        parsed_url = urlparse(link.get("href"))
        if parsed_url.netloc == "":
            parsed_url = parsed_url._replace(netloc=parsed_parent_url.netloc)

        if parsed_url.scheme == "":
            new_scheme = parsed_parent_url.scheme
            parsed_url = parsed_url._replace(scheme=new_scheme)
        elif parsed_url.scheme not in {"http", "https"}:
            continue

        file_extension = parsed_url.path.split(".")[-1].lower()
        if file_extension in ignored_extensions:
            continue

        parsed_url = parsed_url._replace(fragment="")

        if parsed_url.netloc != parsed_parent_url.netloc:
            continue

        next_urls.add(parsed_url.geturl())

    return doc, list(next_urls)


def _get_ip_address(url):
    url = urlparse(url).netloc
    try:
        ip_address = socket.gethostbyname(url)
        return ip_address
    except socket.gaierror as e:
        print(e)
        return None


def _get_geolocation_info(ip_address):
    if ip_address is None:
        return None

    url = f"https://ipinfo.io/{ip_address}/json"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    geolocation_data = response.json()
    return geolocation_data


def crawl_url(url, parent):
    start = time.time()
    response = requests.get(url)
    end = time.time()

    doc, next_urls = _crawl_url(response)
    lang_mentions_count = _count_language_mentions(response.text)
    lang_string = json.dumps(lang_mentions_count)
    ip_address = _get_ip_address(url)
    geolocation = _get_geolocation_info(ip_address)

    result = {
        "url": url,
        "parent": parent,
        "start": start,
        "end": end,
        "languages": lang_string,
        "ip_address": ip_address,
        "geolocation": geolocation["region"] if geolocation else None,
    }
    return result, next_urls


def crawl(hostname, limit=50):
    """Crawl a website recursively and concurrently
    1. Crawl the url, stored the content in a dict, return a list of
       urls to crawl next
    2. Append the crawling task into end of task array.
    3. Start them together and wait for the result.
    4. Run until no more url to crawl, or until limit is reached.

        hostname: the url to crawl
        limit: the maximum number of urls to return

    Returns a list of result dicts with columns
    'start', 'end', 'parent', 'doc', 'ip_address', 'geoloction'
    """

    visited_lock = threading.Lock()
    visited = set()  # includes both success and failed websites

    results_lock = threading.Lock()
    results = {}  # only includes successes

    futures_lock = threading.Lock()
    futures = set()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        with visited_lock:
            visited.add(hostname)
        with futures_lock:
            futures.add(executor.submit(crawl_url, hostname, None))

        while futures:
            for future in concurrent.futures.as_completed(futures):
                with futures_lock:
                    futures.remove(future)

                if future.exception():
                    print(future.exception())
                    continue

                with results_lock:
                    result, next_urls = future.result()
                    url = result["url"]
                    results[url] = result

                for next_url in next_urls:
                    with visited_lock:
                        if len(visited) >= limit:
                            break
                        elif next_url in visited:
                            continue
                        else:
                            visited.add(next_url)

                    print("Crawling", next_url)
                    with futures_lock:
                        futures.add(executor.submit(crawl_url, next_url, url))

    return results
