"""
GitHub to Render Connection Setup and Verification

This script helps verify and setup the connection between your GitHub repository
and Render deployment, ensuring automatic updates when you push to GitHub.
"""

import os
import sys
import json
import subprocess
import requests

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_git_repo():
    """Check if the current directory is a Git repository."""
    try:
        result = subprocess.run(['git', 'status'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             text=True)
        return result.returncode == 0
    except:
        return False

def get_git_remote_url():
    """Get the remote URL for the Git repository."""
    try:
        result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except:
        return None

def get_current_branch():
    """Get the current Git branch."""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except:
        return None

def check_render_yaml():
    """Check if render.yaml exists and has GitHub integration."""
    if not os.path.exists('render.yaml'):
        return False, "render.yaml file not found"
    
    try:
        with open('render.yaml', 'r') as f:
            content = f.read()
        
        has_repo = 'repo:' in content
        has_branch = 'branch:' in content
        
        if has_repo and has_branch:
            return True, "GitHub integration found in render.yaml"
        elif has_repo:
            return False, "repo found but branch missing in render.yaml"
        elif has_branch:
            return False, "branch found but repo missing in render.yaml"
        else:
            return False, "No GitHub integration found in render.yaml"
    except:
        return False, "Failed to read render.yaml"

def check_render_connection(render_url):
    """Check if Render service is accessible."""
    try:
        response = requests.get(render_url, timeout=10)
        return response.status_code < 400, f"Status code: {response.status_code}"
    except requests.RequestException as e:
        return False, f"Connection error: {str(e)}"
    except:
        return False, "Unknown error checking Render connection"

def update_render_yaml(github_url, branch):
    """Update render.yaml with GitHub information."""
    if not os.path.exists('render.yaml'):
        print("render.yaml not found. Creating a new file...")
        with open('render.yaml', 'w') as f:
            f.write(f"""# Render configuration file
# This file defines the services for the ePetCare application

services:
  # Web service for the ePetCare Django application
  - type: web
    name: epetcare
    env: python
    repo: {github_url}
    branch: {branch}
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: gunicorn epetcare.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.0
      - key: WEB_CONCURRENCY
        value: 4  # Number of Gunicorn workers
      - key: DJANGO_SETTINGS_MODULE
        value: epetcare.settings_production
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: epetcare_db
          property: connectionString
      - key: ALLOWED_HOST
        sync: false  # Set this manually in Render dashboard

# Database for the application
databases:
  - name: epetcare_db
    databaseName: epetcare
    user: epetcare
    plan: free  # Use the appropriate plan based on your needs
""")
        return True, "Created new render.yaml with GitHub integration"
    
    try:
        with open('render.yaml', 'r') as f:
            content = f.readlines()
        
        new_content = []
        found_web_service = False
        repo_added = False
        branch_added = False
        
        for line in content:
            if 'type: web' in line:
                found_web_service = True
                new_content.append(line)
            elif found_web_service and 'name:' in line and not repo_added:
                new_content.append(line)
                new_content.append(f"    repo: {github_url}\n")
                new_content.append(f"    branch: {branch}\n")
                repo_added = True
                branch_added = True
            elif 'repo:' in line and found_web_service:
                new_content.append(f"    repo: {github_url}\n")
                repo_added = True
            elif 'branch:' in line and found_web_service:
                new_content.append(f"    branch: {branch}\n")
                branch_added = True
            else:
                new_content.append(line)
        
        with open('render.yaml', 'w') as f:
            f.writelines(new_content)
        
        return True, "Updated render.yaml with GitHub integration"
    except:
        return False, "Failed to update render.yaml"

def get_render_url_from_config():
    """Get Render URL from config.json."""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        remote_db = config.get('remote_database', {})
        url = remote_db.get('url', '')
        
        if url:
            return url
        return None
    except:
        return None

def main():
    print_header("GitHub to Render Connection Setup")
    
    # Check if the current directory is a Git repository
    is_git_repo = check_git_repo()
    print(f"Git repository: {'Found' if is_git_repo else 'Not found'}")
    
    if not is_git_repo:
        print("\nThis directory is not a Git repository.")
        print("Initialize Git repository first? (y/n)")
        if input().lower() == 'y':
            subprocess.run(['git', 'init'])
            print("Git repository initialized.")
        else:
            print("Exiting...")
            return
    
    # Get Git remote URL and branch
    github_url = get_git_remote_url()
    print(f"GitHub remote URL: {github_url if github_url else 'Not found'}")
    
    if not github_url:
        print("\nNo GitHub remote URL found.")
        print("Please enter your GitHub repository URL (e.g., https://github.com/username/repo.git):")
        new_url = input().strip()
        
        if new_url:
            try:
                subprocess.run(['git', 'remote', 'add', 'origin', new_url])
                github_url = new_url
                print(f"Added remote URL: {new_url}")
            except:
                print("Failed to add remote URL")
                return
        else:
            print("No URL provided. Exiting...")
            return
    
    branch = get_current_branch()
    print(f"Current branch: {branch if branch else 'Unknown'}")
    
    if not branch:
        branch = 'main'
        print(f"Using default branch: {branch}")
    
    # Check render.yaml
    render_yaml_ok, render_yaml_msg = check_render_yaml()
    print(f"render.yaml GitHub integration: {render_yaml_msg}")
    
    if not render_yaml_ok:
        print("\nUpdating render.yaml with GitHub integration...")
        update_ok, update_msg = update_render_yaml(github_url, branch)
        print(f"Update result: {update_msg}")
    
    # Check Render connection
    render_url = get_render_url_from_config()
    if render_url:
        print(f"\nChecking connection to Render ({render_url})...")
        connection_ok, connection_msg = check_render_connection(render_url)
        print(f"Connection status: {connection_msg}")
    
    # Print summary and next steps
    print_header("Summary and Next Steps")
    
    if not render_yaml_ok and update_ok:
        print("✅ render.yaml has been updated with GitHub integration")
    elif render_yaml_ok:
        print("✅ render.yaml already has GitHub integration")
    else:
        print("❌ Failed to update render.yaml")
    
    print("\nNext Steps:")
    print("1. Commit and push your changes to GitHub:")
    print("   git add .")
    print("   git commit -m \"Updated Render configuration\"")
    print("   git push origin main")
    print("\n2. In the Render dashboard, connect your GitHub repository:")
    print("   - Go to Dashboard > New > Web Service")
    print("   - Select GitHub")
    print("   - Choose your repository")
    print("   - Render will automatically detect your render.yaml configuration")
    
    print("\n3. After deployment, verify the database connection:")
    print("   - Run python migrate_to_render.py to migrate your database")
    print("   - Check that the API endpoints are accessible")
    print("   - Verify that data synchronization works properly")
    
    print("\nSee GITHUB_TO_RENDER_DB.md for more detailed instructions")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")