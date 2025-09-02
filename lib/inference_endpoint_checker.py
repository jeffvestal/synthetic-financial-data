"""
Inference Endpoint Checker for Elasticsearch ELSER

This module provides functionality to check if inference endpoints (like ELSER)
are deployed and ready to handle requests before attempting to ingest documents
with semantic_text fields.
"""

import time
import requests
from typing import Tuple, Optional
import warnings

# Suppress urllib3 warnings
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')
warnings.filterwarnings('ignore', message='Connecting to.*using TLS with verify_certs=False')


class InferenceEndpointChecker:
    """Checks and waits for inference endpoints to be ready."""
    
    def __init__(self, es_endpoint: str, api_key: str):
        """
        Initialize the checker.
        
        Args:
            es_endpoint: Elasticsearch endpoint URL
            api_key: Elasticsearch API key
        """
        self.es_endpoint = es_endpoint.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json"
        }
        self._endpoint_cache = {}
    
    def wait_for_endpoint(
        self, 
        endpoint_name: str = '.elser-2-elasticsearch',
        max_wait_seconds: int = 300,
        test_input: str = "test"
    ) -> Tuple[bool, str]:
        """
        Wait for an inference endpoint to be deployed and ready.
        
        Args:
            endpoint_name: Name of the inference endpoint
            max_wait_seconds: Maximum time to wait (default: 5 minutes)
            test_input: Test text to send to endpoint
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check cache first
        if endpoint_name in self._endpoint_cache:
            if self._endpoint_cache[endpoint_name]:
                return True, f"Endpoint '{endpoint_name}' ready (cached)"
        
        url = f"{self.es_endpoint}/_inference/sparse_embedding/{endpoint_name}"
        test_payload = {"input": test_input}
        
        print(f"🔍 Checking inference endpoint: {endpoint_name}")
        
        attempt = 0
        start_time = time.time()
        
        while True:
            attempt += 1
            elapsed = time.time() - start_time
            
            if elapsed > max_wait_seconds:
                error_msg = f"❌ Timeout after {max_wait_seconds}s waiting for endpoint '{endpoint_name}'"
                return False, error_msg
            
            print(f"⏳ Polling endpoint... (Attempt #{attempt}, {elapsed:.1f}s elapsed)")
            
            try:
                response = requests.post(
                    url, 
                    headers=self.headers, 
                    json=test_payload, 
                    timeout=15,
                    verify=False  # For development - matches ES client config
                )
                
                # Check if request was successful
                response.raise_for_status()
                
                # Cache successful result
                self._endpoint_cache[endpoint_name] = True
                
                success_msg = f"✅ Endpoint '{endpoint_name}' is ready! (took {elapsed:.1f}s)"
                print(success_msg)
                return True, success_msg
                
            except requests.exceptions.RequestException as e:
                status = getattr(e.response, 'status_code', None) if e.response else None
                
                # Handle different error types
                if status == 404:
                    error_msg = f"❌ Endpoint '{endpoint_name}' not found (404). Check if it exists in Kibana."
                    return False, error_msg
                    
                elif status == 401:
                    error_msg = f"❌ Unauthorized (401). Check your API key permissions."
                    return False, error_msg
                    
                elif status and 400 <= status < 500:
                    error_msg = f"❌ Client error ({status}). This is likely a permanent issue."
                    return False, error_msg
                
                # For server errors (5xx) or network issues, continue retrying
                print(f"⚠️  Error {status or 'network'}: {str(e)[:100]}... Retrying in 10s")
                
                # Wait before retry with exponential backoff (capped at 30s)
                wait_time = min(10 * (1.2 ** (attempt - 1)), 30)
                time.sleep(wait_time)
    
    def check_endpoint_exists(self, endpoint_name: str = '.elser-2-elasticsearch') -> Tuple[bool, str]:
        """
        Quick check if an endpoint exists (without test inference).
        
        Args:
            endpoint_name: Name of the inference endpoint
            
        Returns:
            Tuple of (exists: bool, message: str)
        """
        url = f"{self.es_endpoint}/_inference/{endpoint_name}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return True, f"Endpoint '{endpoint_name}' exists"
            elif response.status_code == 404:
                return False, f"Endpoint '{endpoint_name}' not found"
            else:
                return False, f"Error checking endpoint: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error checking endpoint: {str(e)[:100]}"
    
    def get_all_endpoints(self) -> Tuple[bool, list]:
        """
        Get list of all inference endpoints.
        
        Returns:
            Tuple of (success: bool, endpoints: list)
        """
        url = f"{self.es_endpoint}/_inference"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            response.raise_for_status()
            data = response.json()
            
            endpoints = []
            if isinstance(data, dict):
                # Extract endpoint names from response
                for service_type in data.values():
                    if isinstance(service_type, dict):
                        endpoints.extend(service_type.keys())
            
            return True, endpoints
            
        except requests.exceptions.RequestException as e:
            return False, [f"Error: {str(e)[:100]}"]


# Convenience functions for use in other scripts
def wait_for_elser_endpoint(
    es_endpoint: str, 
    api_key: str, 
    max_wait_seconds: int = 300
) -> Tuple[bool, str]:
    """
    Convenience function to wait for the default ELSER endpoint.
    
    Args:
        es_endpoint: Elasticsearch endpoint URL
        api_key: Elasticsearch API key
        max_wait_seconds: Maximum time to wait
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    checker = InferenceEndpointChecker(es_endpoint, api_key)
    return checker.wait_for_endpoint('.elser-2-elasticsearch', max_wait_seconds)


def check_elser_exists(es_endpoint: str, api_key: str) -> Tuple[bool, str]:
    """
    Convenience function to check if ELSER endpoint exists.
    
    Args:
        es_endpoint: Elasticsearch endpoint URL
        api_key: Elasticsearch API key
        
    Returns:
        Tuple of (exists: bool, message: str)
    """
    checker = InferenceEndpointChecker(es_endpoint, api_key)
    return checker.check_endpoint_exists('.elser-2-elasticsearch')


def list_inference_endpoints(es_endpoint: str, api_key: str) -> Tuple[bool, list]:
    """
    Convenience function to list all inference endpoints.
    
    Args:
        es_endpoint: Elasticsearch endpoint URL
        api_key: Elasticsearch API key
        
    Returns:
        Tuple of (success: bool, endpoints: list)
    """
    checker = InferenceEndpointChecker(es_endpoint, api_key)
    return checker.get_all_endpoints()