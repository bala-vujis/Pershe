import requests
import sys
import json
from datetime import datetime

class SheetPersonalizerAPITester:
    def __init__(self, base_url="https://sheet-magic-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_signup(self):
        """Test user signup"""
        success, response = self.run_test(
            "User Signup",
            "POST",
            "auth/signup",
            200,
            data={
                "name": "Test User",
                "email": self.test_email,
                "password": "password123"
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            if 'user' in response and 'id' in response['user']:
                self.user_id = response['user']['id']
                print(f"   Token obtained: {self.token[:20]}...")
                print(f"   User ID: {self.user_id}")
            return True
        return False

    def test_login(self):
        """Test user login with the same credentials"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_email,
                "password": "password123"
            }
        )
        return success

    def test_get_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_credit_balance(self):
        """Test get credit balance - should be 50 for new users"""
        success, response = self.run_test(
            "Get Credit Balance",
            "GET",
            "credits/balance",
            200
        )
        
        if success and 'balance' in response:
            balance = response['balance']
            print(f"   Credit balance: {balance}")
            if balance == 50:
                print("   ✅ Correct initial balance (50 credits)")
            else:
                print(f"   ⚠️  Expected 50 credits, got {balance}")
        
        return success

    def test_credit_history(self):
        """Test get credit history"""
        success, response = self.run_test(
            "Get Credit History",
            "GET",
            "credits/history",
            200
        )
        return success

    def test_projects_list(self):
        """Test list projects - should be empty initially"""
        success, response = self.run_test(
            "List Projects",
            "GET",
            "projects",
            200
        )
        
        if success and 'projects' in response:
            projects = response['projects']
            print(f"   Projects count: {len(projects)}")
            if len(projects) == 0:
                print("   ✅ Correct initial state (no projects)")
        
        return success

    def test_runs_list(self):
        """Test list runs - should be empty initially"""
        success, response = self.run_test(
            "List Runs",
            "GET",
            "runs",
            200
        )
        
        if success and 'runs' in response:
            runs = response['runs']
            print(f"   Runs count: {len(runs)}")
            if len(runs) == 0:
                print("   ✅ Correct initial state (no runs)")
        
        return success

    def test_google_oauth_status(self):
        """Test Google OAuth connection status"""
        success, response = self.run_test(
            "Google OAuth Status",
            "GET",
            "oauth/google/status",
            200
        )
        
        if success and 'connected' in response:
            connected = response['connected']
            print(f"   Google connected: {connected}")
            if not connected:
                print("   ✅ Expected state (not connected initially)")
        
        return success

    def test_api_keys_list(self):
        """Test list API keys - should be empty initially"""
        success, response = self.run_test(
            "List API Keys",
            "GET",
            "settings/api-keys",
            200
        )
        
        if success and 'keys' in response:
            keys = response['keys']
            print(f"   API keys count: {len(keys)}")
        
        return success

    def test_save_api_key(self):
        """Test saving an OpenAI API key"""
        success, response = self.run_test(
            "Save OpenAI API Key",
            "POST",
            "settings/api-keys",
            200,
            data={
                "provider": "openai",
                "key": "sk-test-dummy-key-12345",
                "nickname": "Test Key"
            }
        )
        return success

    def test_api_keys_list_after_save(self):
        """Test list API keys after saving one"""
        success, response = self.run_test(
            "List API Keys After Save",
            "GET",
            "settings/api-keys",
            200
        )
        
        if success and 'keys' in response:
            keys = response['keys']
            print(f"   API keys count: {len(keys)}")
            if len(keys) == 1:
                print("   ✅ API key saved successfully")
                key = keys[0]
                print(f"   Provider: {key.get('provider')}")
                print(f"   Nickname: {key.get('nickname')}")
        
        return success

def main():
    print("🚀 Starting Sheet Personalizer API Tests")
    print("=" * 50)
    
    tester = SheetPersonalizerAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Root Endpoint", tester.test_root_endpoint),
        ("User Signup", tester.test_signup),
        ("User Login", tester.test_login),
        ("Get Current User", tester.test_get_me),
        ("Credit Balance", tester.test_credit_balance),
        ("Credit History", tester.test_credit_history),
        ("List Projects", tester.test_projects_list),
        ("List Runs", tester.test_runs_list),
        ("Google OAuth Status", tester.test_google_oauth_status),
        ("List API Keys", tester.test_api_keys_list),
        ("Save API Key", tester.test_save_api_key),
        ("List API Keys After Save", tester.test_api_keys_list_after_save),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        failed = tester.tests_run - tester.tests_passed
        print(f"❌ {failed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())