from crawl import crawl
from format import format_result, save_formatted_result


def main(sites, filepath, limit_per_page):
    formatted_results = []
    for site in sites:
        result = crawl(site, limit_per_page)
        formatted_result = format_result(site, result)
        formatted_results += formatted_result

    save_formatted_result(filepath, formatted_results)


if __name__ == "__main__":
    sites = [
        "http://paulgraham.com",
        "https://www.benkuhn.net",
        "https://danluu.com",
        "https://emptysqua.re/blog/",
        "https://astral.sh/blog",
        "https://go.dev",
        "https://www.ekzhang.com",
        "https://gwern.net",
        "https://evjang.com",
    ]

    filepath = "result.csv"
    limit_per_page = 500
    main(sites, filepath, limit_per_page)
