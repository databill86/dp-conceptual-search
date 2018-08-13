import math
import os

MAX_VISIBLE_PAGINATOR_LINK = int(os.getenv("MAX_VISIBLE_PAGINATOR_LINK", 5))
RESULTS_PER_PAGE = int(os.getenv("RESULTS_PER_PAGE", 10))


class Paginator(object):
    """
    Paginator class - replicates pagination functionality from babbage
    """

    def __init__(
            self,
            number_of_results: int,
            max_visible_links: int,
            current_page: int,
            result_per_page: int) -> None:

        self.current_page = current_page
        self.number_of_pages = Paginator.calculate_number_of_pages(
            number_of_results, result_per_page)
        self.end = Paginator.calculate_end(
            self.number_of_pages, current_page, max_visible_links)
        self.start = Paginator.calculate_start(
            self.number_of_pages, max_visible_links, self.end)
        self.pages = self.get_page_list()
        self.size = int(result_per_page)

    @staticmethod
    def calculate_end(
            number_of_pages: int,
            current_page: int,
            max_visible: int) -> int:
        max_pages = number_of_pages
        if max_pages < max_visible:
            return int(max_pages)
        # Half of the pages are visible after current page
        end = float(current_page) + math.ceil(float(max_visible) / 2.0)

        end = max_pages if end > max_pages else end
        end = max_visible if end < max_visible else end
        return int(end)

    @staticmethod
    def calculate_start(
            number_of_pages: int,
            max_visible: int,
            end: int) -> int:
        if number_of_pages <= max_visible:
            return 1
        start = float(end) - float(max_visible) + 1
        return int(max(start, 1))

    @staticmethod
    def calculate_number_of_pages(
            number_of_results: int,
            results_per_page: int) -> int:
        return int(
            math.ceil(
                float(number_of_results) /
                float(results_per_page)))

    def get_page_list(self):
        page_list = range(self.start, self.end + 1)
        return page_list

    def to_dict(self) -> dict:
        return self.__json__()

    def __json__(self) -> dict:
        return {
            "numberOfPages": self.number_of_pages,
            "currentPage": self.current_page,
            "start": self.start,
            "end": self.end,
            "pages": self.pages
        }