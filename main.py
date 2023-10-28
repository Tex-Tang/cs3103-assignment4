from crawl import crawl
from format import (
    format_result,
    print_formatted_result,
    save_formatted_result,
)

result = crawl("http://paulgraham.com")

formatted_result = format_result("http://paulgraham.com", result)
print_formatted_result(formatted_result)
save_formatted_result("result.csv", formatted_result)
