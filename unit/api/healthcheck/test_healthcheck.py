"""
Tests the healthcheck API correctly calls the underlying Elasticsearch client
"""
from unittest import mock

from unit.utils.test_app import TestApp
from unit.elasticsearch.elasticsearch_test_utils import (
    mock_health_check_client_green,
    mock_health_check_client_yellow,
    mock_health_check_client_red,
    mock_health_check_client_exception,
    mock_health_response
)

from app.elasticsearch.elasticsearch_client_service import ElasticsearchClientService


class HealthCheckTestCase(TestApp):

    def setUp(self):
        super(HealthCheckTestCase, self).setUp()

    @mock.patch.object(ElasticsearchClientService, '_init_client', mock_health_check_client_green)
    def test_healthcheck_green(self):
        """
        Tests that the healthcheck makes the correct client call for a cluster health status of 'green'
        :return:
        """
        # Build the target URL
        target = "/healthcheck"

        # Make the request
        request, response = self.get(target, 200)
        expected_response = mock_health_response("green")

        # Check the mock client was called with the correct arguments
        # Assert search was called with correct arguments
        self.mock_client.cluster.health.assert_called_with()

        # Check the response JSON matches the mock response
        self.assertTrue(hasattr(response, "json"), "response should contain JSON property")

        response_json = response.json
        self.assertIsNotNone(response_json, "response json should not be none")
        self.assertIsInstance(response_json, dict, "response json should be instanceof dict")

        self.assertEqual(response_json, expected_response, "returned JSON should match mock response")

    @mock.patch.object(ElasticsearchClientService, '_init_client', mock_health_check_client_yellow)
    def test_healthcheck_yellow(self):
        """
        Tests that the healthcheck makes the correct client call for a cluster health status of 'yellow'
        :return:
        """
        # Build the target URL
        target = "/healthcheck"

        # Make the request
        request, response = self.get(target, 200)
        expected_response = mock_health_response("yellow")

        # Check the mock client was called with the correct arguments
        # Assert search was called with correct arguments
        self.mock_client.cluster.health.assert_called_with()

        # Check the response JSON matches the mock response
        self.assertTrue(hasattr(response, "json"), "response should contain JSON property")

        response_json = response.json
        self.assertIsNotNone(response_json, "response json should not be none")
        self.assertIsInstance(response_json, dict, "response json should be instanceof dict")

        self.assertEqual(response_json, expected_response, "returned JSON should match mock response")

    @mock.patch.object(ElasticsearchClientService, '_init_client', mock_health_check_client_red)
    def test_healthcheck_red(self):
        """
        Tests that the healthcheck makes the correct client call for a cluster health status of 'red'
        :return:
        """
        # Build the target URL
        target = "/healthcheck"

        # Make the request
        request, response = self.get(target, 500)
        expected_response = mock_health_response("red")

        # Check the mock client was called with the correct arguments
        # Assert search was called with correct arguments
        self.mock_client.cluster.health.assert_called_with()

        # Check the response JSON matches the mock response
        self.assertTrue(hasattr(response, "json"), "response should contain JSON property")

        response_json = response.json
        self.assertIsNotNone(response_json, "response json should not be none")
        self.assertIsInstance(response_json, dict, "response json should be instanceof dict")

        self.assertEqual(response_json, expected_response, "returned JSON should match mock response")

    @mock.patch.object(ElasticsearchClientService, '_init_client', mock_health_check_client_exception)
    def test_healthcheck_red(self):
        """
        Tests that the healthcheck API returns a 500 with the correct response body when an exception is raised
        by the client
        :return:
        """
        # Build the target URL
        target = "/healthcheck"

        # Make the request
        request, response = self.get(target, 500)
        expected_response = {
            "elasticsearch": "unavailable"
        }

        # Check the mock client was called with the correct arguments
        # Assert search was called with correct arguments
        self.mock_client.cluster.health.assert_called_with()

        # Check the response JSON matches the mock response
        self.assertTrue(hasattr(response, "json"), "response should contain JSON property")

        response_json = response.json
        self.assertIsNotNone(response_json, "response json should not be none")
        self.assertIsInstance(response_json, dict, "response json should be instanceof dict")

        self.assertEqual(response_json, expected_response, "returned JSON should match mock response")