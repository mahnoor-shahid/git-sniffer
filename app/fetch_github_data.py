import requests
from tqdm import tqdm
import os
import subprocess
import csv
from app.process_metadata import structure_metadata

class GitHubRepoFetcher:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com/search/repositories"
        self.headers = {'Authorization': f'token {self.token}'}
        self.urls = set()
        self.data_dir = os.path.join(os.getcwd(), 'data')

        if not self.validate_token():
            raise ValueError("Invalid GitHub token provided.")  # Raise an error to indicate invalid token
        

    def validate_token(self):
        """ Check if the provided token is valid by making a request to the /user endpoint. """
        try:
            response = requests.get('https://api.github.com/user', headers=self.headers)
            if response.status_code == 200:
                print("Token is valid.")
                return True
            elif response.status_code == 401:
                print("Invalid token.")
                return False
            else:
                print(f"Failed to validate token: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error during token validation: {e}")
            return False


    def fetch_repos(self, search_terms, max_repos):
        # Create a single CSV file for all search terms
        metadata_dir = os.path.join(self.data_dir, 'metadata')
        if not os.path.exists(metadata_dir):
            os.makedirs(metadata_dir)

        combined_csv_filename = os.path.join(metadata_dir, 'combined_metadata.csv')
        file_exists = os.path.isfile(combined_csv_filename)

        with open(combined_csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = None

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

                            # Dynamically get all metadata keys
                            if writer is None:
                                fieldnames = list(item.keys()) + ['params']
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                if not file_exists:
                                    writer.writeheader()

                            # Add the search term to the item data
                            item['params'] = params

                            # Write the repository metadata
                            writer.writerow(item)
                            fetched_urls += 1
                            pbar.update(1)

                        if fetched_urls >= max_repos:
                            break
                    page += 1

                pbar.close()

        structure_metadata(combined_csv_filename)


    def fetch_readme(self, readme_flag):
        self.readme_flag = readme_flag
        if self.readme_flag:
            self.readme_directory = os.path.join(os.getcwd(), 'data', 'readme')
            if not os.path.exists(self.readme_directory):
                os.makedirs(self.readme_directory)
            
            readme_variants = ['README.md', 'README.rst', 'README.txt', 'README']
            
            for url in self.urls:
                repo_owner, repo_name = self._parse_github_url(url)
                
                for readme_variant in readme_variants:
                    readme_url = f'https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/{readme_variant}'
                    response = requests.get(readme_url)

                    if response.status_code == 404:
                        # Try with 'master' if 'main' branch doesn't exist
                        readme_url = f'https://raw.githubusercontent.com/{repo_owner}/{repo_name}/master/{readme_variant}'
                        response = requests.get(readme_url)

                    if response.status_code == 200:
                        self._save_readme(repo_owner, repo_name, response.text)
                        print(f"Successfully fetched {readme_variant} for {repo_name}")
                        break
                else:
                    print(f"Failed to fetch any README for {repo_name}")


    def _parse_github_url(self, url):
        parts = url.rstrip('/').split('/')
        return parts[-2], parts[-1]

    def _save_readme(self, repo_owner, repo_name, content):
        readme_path = os.path.join(self.readme_directory, f'{repo_owner}++{repo_name}_README.md')
        with open(readme_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def clone_repositories(self):
        repos_directory = os.path.join(os.getcwd(), 'data', 'repos')
        if not os.path.exists(repos_directory):
            os.makedirs(repos_directory)
        for url in self.urls:
            repo_name = url.split('/')[-1]
            repo_path = os.path.join(repos_directory, repo_name)
            if not os.path.exists(repo_path):
                subprocess.run(['git', 'clone', url, repo_path])

    def analyze(self, analyze_flag):
        self.analyze_flag = analyze_flag
        if self.analyze_flag:
            self.analysis_directory = os.path.join(os.getcwd(), 'data', 'analysis')
            if not os.path.exists(self.analysis_directory):
                os.makedirs(self.analysis_directory)
            

