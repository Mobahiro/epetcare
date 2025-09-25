"""
Test the connection to the Render API and provide diagnostics
"""
import requests
import json
import os
import sys
import time

def print_section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def print_result(name, success, details=""):
    icon = "✅" if success else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")

def load_config():
    """Load configuration from file."""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error: Failed to load config from {config_path}: {e}")
        return None

def test_url(url, timeout=5):
    """Test if a URL is accessible."""
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url, timeout=timeout)
        status_code = response.status_code
        
        print(f"Response status code: {status_code}")
        
        if status_code == 200:
            print("URL is accessible")
            try:
                content_type = response.headers.get('Content-Type', '')
                print(f"Content-Type: {content_type}")
                
                if 'json' in content_type:
                    data = response.json()
                    print(f"Response data: {json.dumps(data, indent=2)[:500]}...")
                elif 'html' in content_type:
                    print(f"Response: HTML content (first 100 chars): {response.text[:100]}...")
                else:
                    print(f"Response: Binary content or other format")
                    
            except Exception as e:
                print(f"Could not parse response: {e}")
                
            return True, status_code, response
        else:
            print(f"URL returned status code {status_code}")
            try:
                print(f"Response: {response.text[:500]}...")
            except:
                pass
            return False, status_code, response
    except requests.RequestException as e:
        print(f"Error accessing URL: {e}")
        return False, None, None

def test_authentication(url, username, password):
    """Test authentication with the API."""
    auth_urls = [
        f"{url}/api-token-auth/",
        f"{url}/api/token/",
        f"{url}/api/auth/",
        f"{url}/auth/token/"
    ]
    
    for auth_url in auth_urls:
        try:
            print(f"\nTrying authentication at {auth_url}")
            response = requests.post(
                auth_url,
                data={'username': username, 'password': password},
                timeout=5
            )
            
            if response.status_code == 200:
                print("Authentication successful!")
                try:
                    data = response.json()
                    token = data.get('token') or data.get('access')
                    print(f"Got token: {token[:10]}...")
                    return True, auth_url
                except:
                    print("Got success response, but no valid token")
            else:
                print(f"Authentication failed with status code {response.status_code}")
                try:
                    print(f"Response: {response.text[:200]}")
                except:
                    pass
                    
        except requests.RequestException as e:
            print(f"Request failed: {e}")
    
    return False, None

def main():
    print_section("ePetCare Render API Connection Test")
    
    # Load configuration
    config = load_config()
    if not config:
        sys.exit(1)
    
    # Get remote database URL
    remote_db = config.get('remote_database', {})
    base_url = remote_db.get('url', '')
    username = remote_db.get('username', '')
    password = remote_db.get('password', '')
    
    if not base_url:
        print("Error: No remote database URL configured")
        sys.exit(1)
    
    print(f"Configured URL: {base_url}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else '<none>'}")
    
    # Clean up the URL
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # Extract the base domain
    if '://' in base_url:
        base_domain = base_url.split('://')[1].split('/')[0]
        protocol = base_url.split('://')[0]
        clean_base = f"{protocol}://{base_domain}"
    else:
        base_domain = base_url.split('/')[0]
        clean_base = f"https://{base_domain}"
    
    print(f"Base domain: {base_domain}")
    print(f"Clean base URL: {clean_base}")
    
    # Test the base domain
    print_section("Testing Base Domain")
    base_success, base_status, _ = test_url(clean_base)
    print_result("Base domain accessible", base_success)
    
    # Test various API endpoints
    print_section("Testing API Endpoints")
    
    test_urls = [
        (f"{clean_base}/api/", "Main API root"),
        (f"{clean_base}/vet_portal/api/", "Vet Portal API"),
        (f"{clean_base}/api/database/sync/", "Database Sync Endpoint"),
        (f"{clean_base}/vet_portal/api/database/sync/", "Vet Portal Database Sync")
    ]
    
    all_failures = True
    working_urls = []
    
    for url, description in test_urls:
        success, status, response = test_url(url)
        print_result(description, success, f"URL: {url}")
        
        if success:
            all_failures = False
            working_urls.append(url)
    
    # Test authentication if any endpoint worked
    if not all_failures and username and password:
        print_section("Testing Authentication")
        auth_success, auth_url = test_authentication(clean_base, username, password)
        print_result("Authentication", auth_success, 
                    f"Working endpoint: {auth_url}" if auth_success else "Failed at all endpoints")
    
    # Provide recommendations
    print_section("Recommendations")
    
    if all_failures:
        print("❌ Could not connect to any API endpoints.")
        print("\nPossible issues:")
        print("1. The Render service might not be running")
        print("2. The URL might be incorrect")
        print("3. The service might be experiencing technical difficulties")
        print("\nSuggestions:")
        print("1. Check if the application is deployed and running on Render")
        print("2. Verify the URL in your configuration")
        print("3. Try accessing the site directly in a browser")
    else:
        print("✅ Successfully connected to at least one API endpoint.")
        print("\nWorking endpoints:")
        for url in working_urls:
            print(f"- {url}")
        
        # Suggest the best URL to use
        if working_urls:
            recommended_url = None
            
            # Prefer the API endpoints in this order
            for preferred in [
                f"{clean_base}/api",
                f"{clean_base}/vet_portal/api",
                f"{clean_base}/api/v1"
            ]:
                if any(url.startswith(preferred) for url in working_urls):
                    recommended_url = preferred
                    break
            
            if recommended_url:
                print(f"\nRecommended API URL for your config.json:")
                print(f"{recommended_url}")
                
                # Show how to update the config
                print("\nRun the following to update your configuration:")
                print(f"python update_config.py")
    
    print("\nDone!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest canceled by user.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()