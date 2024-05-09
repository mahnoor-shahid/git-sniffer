import requests
from tqdm import tqdm
import os
import subprocess

class GitHubRepoFetcher:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com/search/repositories"
        self.headers = {'Authorization': f'token {self.token}'}
        self.urls = set() # Use a set to avoid duplicates

    def fetch_repos(self, search_terms, max_repos=100):

        for term in search_terms:
            query = term.strip()
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc"
            }
            page = 1
            fetched_urls = 0
            pbar = tqdm(desc=f"Fetching URLs for '{term}'", unit="url")

            while fetched_urls < max_repos:
                params['page'] = page
                response = requests.get(self.base_url, headers=self.headers, params=params)
                if response.status_code != 200:
                    print(f"Failed to fetch data for '{term}': {response.status_code}")
                    break
                data = response.json()
                for item in data.get('items', []):
                    if item['html_url'] not in self.urls:
                        self.urls.add(item['html_url'])
                        pbar.update(1)
                        fetched_urls += 1
                    if fetched_urls >= max_repos:
                        break
                page += 1

            pbar.close()

    def clone_repositories(self):
        if os.path
        for url in self.urls:
            repo_name = url.split('/')[-1]
            repo_path = os.path.join(target_dir, repo_name)
            if not os.path.exists(repo_path):
                subprocess.run(['git', 'clone', url, repo_path])

    # Example usage:
    # clone_repositories(urls, '/path/to/save/repos')

