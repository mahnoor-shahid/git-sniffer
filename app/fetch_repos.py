import requests
from tqdm import tqdm

class GitHubRepoFetcher:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com/search/repositories"
        self.headers = {'Authorization': f'token {self.token}'}

    def fetch_repos(self, search_terms, max_repos=100):
        repos_urls = set()  # Use a set to avoid duplicates
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
                    if item['html_url'] not in repos_urls:
                        repos_urls.add(item['html_url'])
                        pbar.update(1)
                        fetched_urls += 1
                    if fetched_urls >= max_repos:
                        break
                page += 1

            pbar.close()

        return list(repos_urls)  # Convert set to list to return
