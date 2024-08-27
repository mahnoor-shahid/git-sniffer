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
        for term in search_terms:
            query = term.strip()
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc"
            }
            
            metadata_dir = os.path.join(self.data_dir, 'metadata')
            if not os.path.exists(metadata_dir):
                os.makedirs(metadata_dir)

            term_csv_filename = os.path.join(metadata_dir, f'{query.replace(" ", "_")}_metadata.csv')
            file_exists = os.path.isfile(term_csv_filename)

            with open(term_csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = None
                pbar = None

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
                                fieldnames = list(item.keys())
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                if not file_exists:
                                    writer.writeheader()

                            # Write the repository metadata
                            writer.writerow(item)
                            pbar.update(1)
                            fetched_urls += 1
                        
                        if fetched_urls >= max_repos:
                            break
                    page += 1

                pbar.close()

            # Call the function to structure the metadata for each file
            structure_metadata(term_csv_filename, search_term=term)


    def get_readme(self):
        readme_directory = os.path.join(os.getcwd(), 'data', 'readme')
        if not os.path.exists(readme_directory):
            os.makedirs(readme_directory)
        
        for url in self.urls:
            repo_name = url.split('/')[-1].replace('.git', '')  # remove .git if present
            repo_path = os.path.join(readme_directory, repo_name)
            
            if not os.path.exists(repo_path):
                os.makedirs(repo_path)
            
            readme_path = os.path.join(repo_path, 'README.md')
            
            if not os.path.exists(readme_path):
                # Using sparse checkout to only clone the README file
                subprocess.run(['git', 'init'], cwd=repo_path)
                subprocess.run(['git', 'remote', 'add', 'origin', url], cwd=repo_path)
                subprocess.run(['git', 'config', 'core.sparseCheckout', 'true'], cwd=repo_path)
                with open(os.path.join(repo_path, '.git', 'info', 'sparse-checkout'), 'w') as f:
                    f.write('README.md\n')
                subprocess.run(['git', 'pull', 'origin', 'main'], cwd=repo_path)  # Assumes the main branch is 'main'


    def clone_repositories(self):
        repos_directory = os.path.join(os.getcwd(), 'data', 'repos')
        if not os.path.exists(repos_directory):
            os.makedirs(repos_directory)
        for url in self.urls:
            repo_name = url.split('/')[-1]
            repo_path = os.path.join(repos_directory, repo_name)
            if not os.path.exists(repo_path):
                subprocess.run(['git', 'clone', url, repo_path])

    # Example usage:
    # clone_repositories(urls, '/path/to/save/repos')

