"""
Unit tests for Django REST API views.

Tests the view functions directly using Django's RequestFactory
to bypass URL routing issues during testing.
"""

import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add the server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app/server'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_config.settings')

import django
from django.test import TestCase, RequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status

# Initialize Django
django.setup()

from app.server.monitoring.views import health_check, receive_telemetry


class TestHealthCheckView(TestCase):
    """Test the health check view function directly."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    def test_health_check_success(self):
        """Test health check view returns success response."""
        request = self.factory.get('/health/')
        response = health_check(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['message'], 'Server is running')
        self.assertEqual(data['service'], 'system-monitor-api')

    def test_health_check_response_structure(self):
        """Test health check response has expected structure."""
        request = self.factory.get('/health/')
        response = health_check(request)
        
        data = response.data
        
        # Verify all expected fields are present
        required_fields = ['status', 'message', 'service']
        for field in required_fields:
            self.assertIn(field, data)
            self.assertIsNotNone(data[field])

    @patch('app.server.monitoring.views.logger')
    def test_health_check_logging(self, mock_logger):
        """Test that health check endpoint logs the request."""
        request = self.factory.get('/health/')
        health_check(request)
        
        # Verify logging was called
        mock_logger.info.assert_called()


class TestTelemetryView(TestCase):
    """Test the telemetry receiving view function directly."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    def test_telemetry_post_success(self):
        """Test successful telemetry data submission."""
        telemetry_data = {
            "timestamp": "2025-01-09T15:30:00Z",
            "hostname": "test-machine",
            "metrics": {
                "cpu": {"usage": 45.2, "cores": 8},
                "memory": {"total": 16384, "available": 8192, "percent": 50.0}
            }
        }
        
        request = self.factory.post(
            '/telemetry/',
            data=json.dumps(telemetry_data),
            content_type='application/json'
        )
        
        # Manually add the parsed data to request (simulating DRF parsing)
        request.data = telemetry_data
        
        response = receive_telemetry(request)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.data
        self.assertEqual(data['status'], 'received')
        self.assertEqual(data['hostname'], 'test-machine')
        self.assertEqual(data['timestamp'], '2025-01-09T15:30:00Z')
        self.assertEqual(data['metrics_count'], 2)

    def test_telemetry_missing_hostname(self):
        """Test telemetry view with missing hostname field."""
        incomplete_data = {
            "timestamp": "2025-01-09T15:30:00Z",
            "metrics": {"cpu": {"usage": 25.0}}
            # Missing hostname
        }
        
        request = self.factory.post(
            '/telemetry/',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        request.data = incomplete_data
        
        response = receive_telemetry(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('hostname', response.data['error'])

    def test_telemetry_missing_metrics(self):
        """Test telemetry view with missing metrics field."""
        incomplete_data = {
            "timestamp": "2025-01-09T15:30:00Z",
            "hostname": "test-agent"
            # Missing metrics
        }
        
        request = self.factory.post(
            '/telemetry/',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        request.data = incomplete_data
        
        response = receive_telemetry(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('metrics', response.data['error'])

    def test_telemetry_missing_timestamp(self):
        """Test telemetry view with missing timestamp field."""
        incomplete_data = {
            "hostname": "test-agent",
            "metrics": {"cpu": {"usage": 25.0}}
            # Missing timestamp
        }
        
        request = self.factory.post(
            '/telemetry/',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        request.data = incomplete_data
        
        response = receive_telemetry(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('timestamp', response.data['error'])

    @patch('app.server.monitoring.views.logger')
    def test_telemetry_logging(self, mock_logger):
        """Test that telemetry view logs received data."""
        telemetry_data = {
            "timestamp": "2025-01-09T15:30:00Z",
            "hostname": "test-agent",
            "metrics": {"cpu": {"usage": 25.0}}
        }
        
        request = self.factory.post('/telemetry/')
        request.data = telemetry_data
        
        receive_telemetry(request)
        
        # Verify logging was called
        mock_logger.info.assert_called()

    def test_telemetry_empty_metrics(self):
        """Test telemetry view with empty metrics object."""
        telemetry_data = {
            "timestamp": "2025-01-09T15:30:00Z",
            "hostname": "test-agent",
            "metrics": {}  # Empty metrics
        }
        
        request = self.factory.post(
            '/telemetry/',
            data=json.dumps(telemetry_data),
            content_type='application/json'
        )
        # Simulate DRF request parsing
        request.data = telemetry_data
        
        response = receive_telemetry(request)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertEqual(data['metrics_count'], 0)


class TestViewBusinessLogic(TestCase):
    """Test the business logic and edge cases of view functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    def test_health_check_response_consistency(self):
        """Test that health check returns consistent data across calls."""
        request = self.factory.get('/health/')
        
        response1 = health_check(request)
        response2 = health_check(request)
        
        self.assertEqual(response1.data, response2.data)
        self.assertEqual(response1.status_code, response2.status_code)

    def test_telemetry_metrics_count_calculation(self):
        """Test that metrics_count is calculated correctly."""
        test_cases = [
            ({"cpu": {}, "memory": {}, "disk": {}}, 3),
            ({"cpu": {}}, 1),
            ({}, 0),
        ]
        
        for metrics, expected_count in test_cases:
            with self.subTest(metrics=metrics, expected_count=expected_count):
                telemetry_data = {
                    "timestamp": "2025-01-09T15:30:00Z",
                    "hostname": "test-agent",
                    "metrics": metrics
                }
                
                request = self.factory.post(
                    '/telemetry/',
                    data=json.dumps(telemetry_data),
                    content_type='application/json'
                )
                # Simulate DRF request parsing
                request.data = telemetry_data
                
                response = receive_telemetry(request)
                
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data['metrics_count'], expected_count)