from elasticsearch_dsl.response import Response
from elasticsearch_dsl.response.hit import Hit, HitMeta

from typing import List

from ons.search.sort_fields import SortFields


class SimpleHit(dict):
    def __init__(self, *args, **kwargs):
        super(SimpleHit, self).__init__(*args, **kwargs)

    def set_value(self, field_name, value):
        if field_name in self:
            self[field_name] = value
        elif "." in field_name:
            parts = field_name.split(".")
            if parts[0] == "description" and len(parts) <= 2:
                self["description"][parts[1]] = value
        else:
            raise Exception("Unable to set field %s" % field_name)


def buckets_to_json(buckets) -> (dict, int):
    """
    Converts aggregation buckets to properly formatted JSON.
    :param buckets:
    :return:
    """
    total = 0

    result = {}
    for item in buckets:
        item_key = item["key"]
        count = item["doc_count"]
        result[item_key] = count
        total += count

    return result, total


def get_var(input_dict: dict, accessor_string: str):
    """
    Gets data from a dictionary using a dotted accessor-string
    :param input_dict:
    :param accessor_string:
    :return:
    """
    current_data = input_dict
    for chunk in accessor_string.split('.'):
        current_data = current_data.get(chunk, {})
        if not isinstance(current_data, dict):
            break
    return current_data


def highlight_all(hits: List[Hit], tag: str="strong", min_token_size: int=2) -> List[SimpleHit]:
    """

    :param hits:
    :param tag:
    :param min_token_size:
    :return:
    """
    from ons.search import fields

    simple_hits = []

    start_tag = "<{tag}>".format(tag=tag)
    end_tag = "</{tag}>".format(tag=tag)

    for hit in hits:
        simple_hit: SimpleHit = SimpleHit(hit.to_dict())
        if hasattr(hit, "meta"):
            meta: HitMeta = hit.meta
            if hasattr(meta, "highlight"):
                highlight_dict = meta.highlight.to_dict()
                for highlight_field in highlight_dict:

                    for fragment in highlight_dict[highlight_field]:
                        if start_tag in fragment and end_tag in fragment:
                            idx_start = fragment.index(start_tag) + len(start_tag)
                            idx_end = fragment.index(end_tag)

                            highlighted_token = fragment[idx_start:idx_end]
                            if len(highlighted_token) > min_token_size:
                                field_value = get_var(simple_hit, highlight_field)

                                if isinstance(field_value, str):
                                    highlighted_val = highlight(highlighted_token, field_value)

                                elif isinstance(field_value, list):
                                    highlighted_val = []
                                    for val in field_value:
                                        highlighted_val.append(highlight(highlighted_token, val))

                                else:
                                    # Unknown field type, continue
                                    continue

                                if field_value == fields.keywords_raw.name:
                                    simple_hit.set_value(fields.keywords.name, highlighted_val)
                                else:
                                    simple_hit.set_value(highlight_field, highlighted_val)

        simple_hits.append(simple_hit)
    return simple_hits


def highlight(highlighted_text: str, val: str, tag: str='strong') -> str:
    """
    Wraps the desired text snippet in :param tag html tags.
    :param highlighted_text:
    :param val:
    :param tag:
    :return:
    """
    import re
    pattern = re.compile(re.escape(highlighted_text), re.I)
    toreplace = "<{tag}>\g<0></{tag}>".format(tag=tag)
    return re.sub(pattern, toreplace, val)


class ONSResponse(Response):
    """
    Class for marshalling Elasticsearch results to JSON expected by babbage
    """

    def featured_result_to_json(self) -> dict:
        return self.response_to_json(1, 1)

    def aggs_to_json(self) -> dict:
        """
        Returns search aggregations as formatted JSON.
        :return:
        """
        if hasattr(self.aggregations, "docCounts"):
            aggs = self.aggregations.__dict__["_d_"]["docCounts"]
            buckets = aggs["buckets"]
            if len(buckets) > 0:
                # Type counts query
                aggregations, total_hits = buckets_to_json(buckets)

                json = {
                    # "numberOfResults": response.hits.total,
                    "numberOfResults": total_hits,
                    "docCounts": aggregations
                }

                return json

        return {}

    def response_to_json(self, page_number: int, page_size: int,
                         sort_by: SortFields=SortFields.relevance) -> dict:
        """
        Builds and returns the full JSON response expected by Babbage.
        :return:
        """
        from ons.search.paginator import Paginator, MAX_VISIBLE_PAGINATOR_LINK

        paginator = Paginator(
            self.hits.total,
            MAX_VISIBLE_PAGINATOR_LINK,
            page_number,
            page_size)

        highlighted_hits = highlight_all(self.hits)

        json = {
            "numberOfResults": self.hits.total,
            "took": self.took,
            "results": highlighted_hits,
            "docCounts": {},
            "paginator": paginator.to_dict(),
            "sortBy": sort_by.name
        }

        return json
