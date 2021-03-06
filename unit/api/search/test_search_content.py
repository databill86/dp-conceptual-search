"""
Tests the ONS content search API
"""
from json import dumps
from typing import List

from unittest import mock

from unit.utils.search_test_app import SearchTestApp
from unit.elasticsearch.elasticsearch_test_utils import mock_search_client, mock_hits_highlighted

from dp_conceptual_search.config import CONFIG
from dp_conceptual_search.ons.search.index import Index
from dp_conceptual_search.search.search_type import SearchType
from dp_conceptual_search.ons.search.sort_fields import query_sort, SortField
from dp_conceptual_search.ons.search.fields import get_highlighted_fields, Field
from dp_conceptual_search.ons.search.content_type import AvailableContentTypes, ContentType
from dp_conceptual_search.app.elasticsearch.elasticsearch_client_service import ElasticsearchClientService
from dp_conceptual_search.ons.search.queries.ons_query_builders import (
    build_content_query, build_function_score_content_query
)


class SearchContentApiTestCase(SearchTestApp):

    @staticmethod
    def paginate():
        """
        Calls paginate and makes some basic assertions
        :return:
        """
        import random

        # Generate a random page number between 1 and 10
        current_page = random.randint(1, 10)

        # Generate a random page size between 11 and 20
        size = random.randint(11, 20)

        # Calculate correct start page number
        from_start = 0 if current_page <= 1 else (current_page - 1) * size

        return from_start, current_page, size

    @property
    def search_term(self):
        """
        Mock search term to be used for testing
        :return:
        """
        return "Zuul"

    @property
    def highlight_dict(self):
        """
        Builds the expected highlight query dict
        :return:
        """
        highlight_fields: List[Field] = get_highlighted_fields()

        highlight_query = {
            "fields": {
                highlight_field.name: {
                    "number_of_fragments": 0,
                    "pre_tags": ["<strong>"],
                    "post_tags": ["</strong>"]
                } for highlight_field in highlight_fields
            }
        }

        return highlight_query

    @mock.patch.object(ElasticsearchClientService, '_init_client', mock_search_client)
    def test_content_query_search_called(self):
        """
        Tests that the search method is called properly by the api for a content query
        :return:
        """
        # Make the request
        # Set pagination params
        from_start, current_page, size = self.paginate()

        # Set sort_by
        sort_by: SortField = SortField.relevance

        # Build params dict
        params = {
            "q": self.search_term,
            "page": current_page,
            "size": size
        }

        # Build post JSON
        data = {
            "sort_by": sort_by.name
        }

        # URL encode
        url_encoded_params = self.url_encode(params)

        target = "/search/content?{q}".format(q=url_encoded_params)

        # Make the request
        request, response = self.post(target, 200, data=dumps(data))

        # Get a list of all available content types
        content_types: List[ContentType] = AvailableContentTypes.available_content_types()

        # Build the filter query
        type_filters = [content_type.name for content_type in content_types]
        filter_query = [
            {
                "terms": {
                    "type": type_filters
                }
            }
        ]

        content_query = build_content_query(self.search_term)

        # Build the expected query dict - note this should not change
        expected = {
            "from": from_start,
            "query": {
                "bool": {
                    "filter": filter_query,
                    "must": [
                        build_function_score_content_query(content_query, content_types).to_dict(),
                    ]
                }
            },
            "size": size,
            "sort": query_sort(SortField.relevance),
            "highlight": self.highlight_dict
        }

        # Assert search was called with correct arguments
        self.mock_client.search.assert_called_with(index=[Index.ONS.value], doc_type=[], body=expected,
                                                   search_type=SearchType.DFS_QUERY_THEN_FETCH.value)

        data = response.json
        results = data['results']

        expected_hits_highlighted = mock_hits_highlighted()
        self.assertEqual(results, expected_hits_highlighted, "returned hits should match expected")

    def test_max_request_size_400(self):
        """
        Test that making a request where the page size if greater than the max allowed raises a 400 BAD_REQUEST
        :return:
        """
        # Make the request
        # Set correct from_start and page size for featured result query
        from_start = 0
        current_page = from_start + 1
        size = CONFIG.SEARCH.max_request_size + 1

        # Set sort_by
        sort_by: SortField = SortField.relevance

        # Build params dict
        params = {
            "q": self.search_term,
            "page": current_page,
            "size": size
        }

        # Build post JSON
        data = {
            "sort_by": sort_by.name
        }

        # URL encode
        url_encoded_params = self.url_encode(params)

        target = "/search/content?{q}".format(q=url_encoded_params)

        # Make the request
        request, response = self.post(target, 400, data=dumps(data))
