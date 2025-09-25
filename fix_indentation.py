"""
ePetCare Remote DB Client Fixer

This script specifically fixes the indentation issue in remote_db_client.py
that causes the "unexpected indent" error.
"""

import os
import sys
import shutil
import re

def main():
    """Fix the indentation issues in remote_db_client.py"""
    # Find the remote_db_client.py file
    client_path = os.path.join('vet_desktop_app', 'utils', 'remote_db_client.py')
    
    if not os.path.exists(client_path):
        print(f"Error: {client_path} not found!")
        return 1
    
    print(f"Found remote_db_client.py at {client_path}")
    
    # Create a backup
    backup_path = client_path + '.bak'
    shutil.copy2(client_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Read the file content
    with open(client_path, 'r') as f:
        content = f.read()
    
    # Check for specific indentation issues in get_database_info method
    if "def get_database_info(self):" in content:
        print("Scanning for indentation issues in get_database_info method...")
        
        # Extract the method content
        method_pattern = r"(def get_database_info\(self\):.*?)(?:def|\Z)"
        match = re.search(method_pattern, content, re.DOTALL)
        
        if match:
            method_content = match.group(1)
            
            # Check for duplication issues
            if method_content.count("return response.json()") > 1:
                print("Found duplicate code blocks in get_database_info method!")
                
                # Replace with a fixed version
                fixed_method = """    def get_database_info(self):
        \"\"\"Get basic information about the remote database\"\"\"
        url = f"{self.base_url}/api/database-info/"
        try:
            response = requests.get(
                url, 
                headers=self.get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get database info: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error connecting to remote database: {str(e)}")
            return None
"""
                # Replace the method in the content
                new_content = re.sub(method_pattern, fixed_method, content, flags=re.DOTALL)
                
                # Write the fixed content back to the file
                with open(client_path, 'w') as f:
                    f.write(new_content)
                
                print("Successfully fixed indentation issues!")
                return 0
            else:
                print("No duplication issues found in get_database_info method.")
        else:
            print("Could not properly extract get_database_info method content.")
            return 1
    else:
        print("get_database_info method not found in file.")
        return 1
    
    # If we get here, no issues were found or fixed
    print("No indentation issues found or fixed.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)