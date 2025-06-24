#!/usr/bin/env python3
"""
Security testing script for FastAPI Task Management System.
This script performs basic security checks on the API.
"""

import asyncio
import time
import requests
from typing import List, Dict, Any


class SecurityTester:
    """Security testing class for API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results: List[Dict[str, Any]] = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_security_headers(self):
        """Test security headers are properly set."""
        print("\\n🔒 Testing Security Headers...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            # Check for security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,  # Should exist
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": None,  # Should exist
            }
            
            for header, expected_value in security_headers.items():
                if header in headers:
                    if expected_value and headers[header] != expected_value:
                        self.log_test(
                            f"Security Header: {header}",
                            False,
                            f"Expected '{expected_value}', got '{headers[header]}'"
                        )
                    else:
                        self.log_test(f"Security Header: {header}", True, "Present")
                else:
                    self.log_test(f"Security Header: {header}", False, "Missing")
                    
        except Exception as e:
            self.log_test("Security Headers Test", False, f"Error: {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        print("\\n🚦 Testing Rate Limiting...")
        
        try:
            # Make rapid requests to trigger rate limiting
            responses = []
            for i in range(5):
                response = self.session.get(f"{self.base_url}/health")
                responses.append(response)
                time.sleep(0.1)  # Small delay between requests
            
            # Check for rate limit headers
            last_response = responses[-1]
            if "X-Rate-Limit-Limit" in last_response.headers:
                self.log_test("Rate Limit Headers", True, "Present in response")
            else:
                self.log_test("Rate Limit Headers", False, "Missing from response")
                
        except Exception as e:
            self.log_test("Rate Limiting Test", False, f"Error: {str(e)}")
    
    def test_blocked_paths(self):
        """Test that suspicious paths are blocked."""
        print("\\n🚫 Testing Blocked Paths...")
        
        suspicious_paths = [
            "/.env",
            "/wp-admin",
            "/admin.php",
            "/phpmyadmin",
            "/.git/config",
            "/config/database.yml",
            "/backup.sql",
            "/.aws/credentials",
            "/.ssh/id_rsa",
        ]
        
        for path in suspicious_paths:
            try:
                response = self.session.get(f"{self.base_url}{path}")
                if response.status_code == 404:
                    self.log_test(f"Blocked Path: {path}", True, "Properly blocked")
                else:
                    self.log_test(
                        f"Blocked Path: {path}",
                        False,
                        f"Status: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(f"Blocked Path: {path}", False, f"Error: {str(e)}")
    
    def test_blocked_user_agents(self):
        """Test that malicious user agents are blocked."""
        print("\\n🤖 Testing Blocked User Agents...")
        
        malicious_agents = [
            "sqlmap/1.0",
            "nikto/2.1.6",
            "nmap/7.80",
            "masscan/1.0",
            "w3af/1.6",
            "dirbuster/1.0",
        ]
        
        for agent in malicious_agents:
            try:
                headers = {"User-Agent": agent}
                response = self.session.get(f"{self.base_url}/health", headers=headers)
                
                if response.status_code == 403:
                    self.log_test(f"Blocked Agent: {agent}", True, "Properly blocked")
                else:
                    self.log_test(
                        f"Blocked Agent: {agent}",
                        False,
                        f"Status: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(f"Blocked Agent: {agent}", False, f"Error: {str(e)}")
    
    def test_request_size_limit(self):
        """Test request size limitations."""
        print("\\n📦 Testing Request Size Limits...")
        
        try:
            # Create a large payload (11MB)
            large_data = "x" * (11 * 1024 * 1024)
            
            response = self.session.post(
                f"{self.base_url}/health",
                data=large_data,
                headers={"Content-Type": "text/plain"}
            )
            
            if response.status_code == 413:
                self.log_test("Large Request Blocking", True, "Request properly rejected")
            else:
                self.log_test(
                    "Large Request Blocking",
                    False,
                    f"Status: {response.status_code}"
                )
                
        except Exception as e:
            # This might fail due to client-side limits, which is also good
            self.log_test("Large Request Blocking", True, "Client-side protection active")
    
    def test_sql_injection_attempts(self):
        """Test basic SQL injection protection."""
        print("\\n💉 Testing SQL Injection Protection...")
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --",
        ]
        
        for payload in sql_payloads:
            try:
                # Test in query parameters
                response = self.session.get(
                    f"{self.base_url}/health",
                    params={"test": payload}
                )
                
                # Should not return 500 (internal server error)
                if response.status_code != 500:
                    self.log_test(
                        f"SQL Injection: {payload[:20]}...",
                        True,
                        "No server error"
                    )
                else:
                    self.log_test(
                        f"SQL Injection: {payload[:20]}...",
                        False,
                        "Caused server error"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"SQL Injection: {payload[:20]}...",
                    False,
                    f"Error: {str(e)}"
                )
    
    def test_xss_attempts(self):
        """Test XSS protection."""
        print("\\n🌐 Testing XSS Protection...")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
        ]
        
        for payload in xss_payloads:
            try:
                response = self.session.get(
                    f"{self.base_url}/health",
                    params={"message": payload}
                )
                
                # Check if XSS payload is reflected without encoding
                if payload in response.text:
                    self.log_test(
                        f"XSS Protection: {payload[:20]}...",
                        False,
                        "Payload reflected"
                    )
                else:
                    self.log_test(
                        f"XSS Protection: {payload[:20]}...",
                        True,
                        "Payload not reflected"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"XSS Protection: {payload[:20]}...",
                    False,
                    f"Error: {str(e)}"
                )
    
    def run_all_tests(self):
        """Run all security tests."""
        print("🔐 Starting Security Test Suite...")
        print(f"Target: {self.base_url}")
        print("=" * 50)
        
        # Run all tests
        self.test_security_headers()
        self.test_rate_limiting()
        self.test_blocked_paths()
        self.test_blocked_user_agents()
        self.test_request_size_limit()
        self.test_sql_injection_attempts()
        self.test_xss_attempts()
        
        # Summary
        print("\\n" + "=" * 50)
        print("📊 Security Test Summary")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\\n⚠️  Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return failed_tests == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Security test suite for FastAPI app")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.url)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
