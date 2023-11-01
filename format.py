import csv


header = ("URL", "DURATION", "IP_ADDRESS", "GEOLOCATION", "LANGUAGES")


def format_result(parent_url, result, prefix=""):
    rows = [
        (
            (prefix + " " if prefix else "") + parent_url,
            "{:.2f}s".format(result[parent_url]["end"] - result[parent_url]["start"]),
            result[parent_url]["ip_address"],
            result[parent_url]["geolocation"],
            result[parent_url]["languages"],
        )
    ]

    children_urls = [
        url
        for url in result
        if "parent" in result[url] and result[url]["parent"] == parent_url
    ]

    for child_url in children_urls:
        rows = rows + format_result(child_url, result, prefix + "--")

    return rows


def print_formatted_result(formatted_result):
    max_lens = [max(map(len, cells)) for cells in zip(*([header] + formatted_result))]

    print("Total crawled urls:", len(formatted_result))

    print(*[cell.ljust(max_lens[i]) for i, cell in enumerate(header)])
    for row in formatted_result:
        print(*[cell.ljust(max_lens[i]) for i, cell in enumerate(row)])


def save_formatted_result(path, formatted_result):
    with open(path, "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(header)
        for row in formatted_result:
            csv_writer.writerow(row)
