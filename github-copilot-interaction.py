import requests
import os
import base64
from pathlib import Path
import json

class GitHubCopilotInteraction:
    def __init__(self, username, pat_token):
        """
        Initialize with GitHub credentials
        
        Args:
            username (str): GitHub username
            pat_token (str): GitHub Personal Access Token with appropriate scopes
        """
        self.username = username
        self.pat_token = pat_token
        self.headers = {
            'Authorization': f'token {pat_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'GitHub-Copilot-Client-{username}'
        }
        self.base_url = 'https://api.github.com'
        
    def fetch_repository(self, repo_owner, repo_name, target_path=None):
        """
        Fetch a GitHub repository and download its contents
        
        Args:
            repo_owner (str): Owner of the repository
            repo_name (str): Name of the repository
            target_path (str, optional): Local path to save the repository contents
                                        Defaults to a directory with the repo name
        
        Returns:
            dict: Information about the downloaded repository
        """
        if target_path is None:
            target_path = Path(repo_name)
        else:
            target_path = Path(target_path)
            
        # Create the target directory if it doesn't exist
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Fetching repository {repo_owner}/{repo_name}...")
        
        # Get repository contents (recursively)
        return self._download_directory_contents(repo_owner, repo_name, '', target_path)
    
    def _download_directory_contents(self, owner, repo, path, target_path):
        """
        Recursively download directory contents
        
        Args:
            owner (str): Repository owner
            repo (str): Repository name
            path (str): Current directory path within the repository
            target_path (Path): Local path to save the contents
        
        Returns:
            dict: Information about downloaded files and directories
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Error fetching directory contents: {response.status_code}")
            print(response.text)
            return {'error': response.text}
        
        contents = response.json()
        result = {'files': [], 'directories': []}
        
        for item in contents:
            item_path = target_path / item['name']
            
            if item['type'] == 'file':
                # Download the file
                file_content = self._get_file_content(item)
                item_path.write_bytes(file_content)
                result['files'].append({
                    'name': item['name'],
                    'path': str(item_path),
                    'size': item['size']
                })
                print(f"Downloaded: {item_path}")
                
            elif item['type'] == 'dir':
                # Create directory and recursively download contents
                item_path.mkdir(exist_ok=True)
                sub_result = self._download_directory_contents(
                    owner, repo, f"{path}/{item['name']}" if path else item['name'], item_path
                )
                result['directories'].append({
                    'name': item['name'],
                    'path': str(item_path),
                    'contents': sub_result
                })
                
        return result
    
    def _get_file_content(self, file_info):
        """
        Decode and return file content from GitHub API response
        
        Args:
            file_info (dict): File information from GitHub API
            
        Returns:
            bytes: Decoded file content
        """
        if 'content' in file_info and file_info['content']:
            return base64.b64decode(file_info['content'])
        
        # If content is not included in the response, fetch it
        response = requests.get(file_info['download_url'], headers=self.headers)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Error downloading file: {response.status_code}")
            return b''
    
    def send_copilot_query(self, query, context_files=None):
        """
        Send a query to GitHub Copilot API
        
        Args:
            query (str): The query/prompt to send to Copilot
            context_files (list, optional): List of file paths to provide as context
            
        Returns:
            dict: Copilot's response
        """
        # Note: This is a placeholder implementation since the specific
        # GitHub Copilot API endpoints and authentication methods aren't
        # officially documented for general use
        
        copilot_url = "https://api.githubcopilot.com/v1/completions"
        
        # Read context files if provided
        context = ""
        if context_files:
            for file_path in context_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        context += f"\n# File: {file_path}\n{file_content}\n"
                except Exception as e:
                    print(f"Error reading context file {file_path}: {e}")
        
        # Prepare request body (this would need adjustment based on actual API specs)
        request_body = {
            "prompt": f"{context}\n{query}",
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        # Special headers for Copilot API
        copilot_headers = {
            **self.headers,
            "Content-Type": "application/json",
            "GitHub-Authentication": f"Bearer {self.pat_token}"
        }
        
        try:
            response = requests.post(copilot_url, headers=copilot_headers, json=request_body)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error from Copilot API: {response.status_code}")
                print(response.text)
                return {"error": response.text}
                
        except Exception as e:
            print(f"Exception when calling Copilot API: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # Replace with your actual credentials
    github_username = "your_username"
    github_pat = "your_personal_access_token"
    
    # Initialize the client
    client = GitHubCopilotInteraction(github_username, github_pat)
    
    # Fetch a repository
    repo_info = client.fetch_repository("octocat", "Hello-World")
    
    # Send a query to Copilot with context from the repository
    # This is a placeholder - would need adjustment for actual Copilot API
    context_files = [
        "Hello-World/README.md",
        "Hello-World/main.py",  # Assuming this exists
    ]
    
    copilot_response = client.send_copilot_query(
        "Write a function to parse JSON data from the GitHub API", 
        context_files
    )
    
    print("\nCopilot Response:")
    print(json.dumps(copilot_response, indent=2))
