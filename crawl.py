import concurrent.futures
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from datetime import datetime


def crawl_url(url: str):
    response = requests.get(url)
    doc = BeautifulSoup(response.content, features="lxml")

    next_urls = set()
    for link in doc.find_all(href=True):
        parsed_url = urlparse(link.get("href"))
        if parsed_url.netloc == "":
            parsed_url = parsed_url._replace(netloc=urlparse(url).netloc)

        if parsed_url.scheme == "":
            parsed_url = parsed_url._replace(scheme=urlparse(url).scheme)

        if parsed_url.netloc == urlparse(url).netloc:
            next_urls.add(parsed_url.geturl())

    return url, doc, list(next_urls)


def crawl(hostname: str, limit=50):
    """Crawl a website recursively and concurrently
    1. Crawl the url, stored the content in a dict, return a list of
       urls to crawl next
    2. Append the crawling task into end of task array.
    3. Start them together and wait for the result.
    4. Run until no more url to crawl

        hostname: the url to crawl
        limit: the maximum number of urls to crawl

        Returns a dict of crawled urls
    """

    result = {}
    futures = set()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        result[hostname] = {
            "start": time.time(),
            "parent": None,
            "seq": len(result) + 1,
        }
        futures.add(executor.submit(crawl_url, hostname))

        while futures:
            for future in concurrent.futures.as_completed(futures):
                futures.remove(future)

                if future.exception():
                    print(future.exception())
                    continue

                url, doc, next_urls = future.result()
                result[url]["end"] = time.time()
                # result[url]["doc"] = doc

                for next_url in next_urls:
                    if len(result) >= limit:
                        continue

                    if next_url in result:
                        continue

                    result[next_url] = {
                        "start": time.time(),
                        "parent": url,
                        "seq": len(result) + 1,
                    }
                    print("Crawling", next_url)
                    futures.add(executor.submit(crawl_url, next_url))

    return result
