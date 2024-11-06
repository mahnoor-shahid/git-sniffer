import requests
from tqdm import tqdm
import os
import subprocess
from langchain.chains import LocalCodeChain

class GitHubRepoFetcher:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com/search/repositories"
        self.headers = {'Authorization': f'token {self.token}'}
        self.urls = set() # Use a set to avoid duplicates
        self.target_dir = os.path.join(os.getcwd(), 'data')

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

        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)
            print(f"Created directory: {self.target_dir}")
        if not self.urls:
            print("Error: No repository URLs are available to clone.")
            return

        pbar = tqdm(total=len(self.urls), desc="Cloning Repositories", unit="repo")

        for url in self.urls:
            repo_name = url.split('/')[-1]
            repo_path = os.path.join(self.target_dir, repo_name)
            if not os.path.exists(repo_path):
                # Clone the repository quietly without showing output
                subprocess.run(['git', 'clone', url, repo_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pbar.update(1)
            else:
                print(f"Repository {repo_name} already exists at {repo_path}")

        pbar.close()

    def analyze_repository(self):
        # Initialize LangChain for local code analysis
        chain = LocalCodeChain(
            base_directory=self.target_dir,
            language_model="openai-davinci-codex",  # Replace with your chosen model
            openai_api_key="YOUR_OPENAI_API_KEY"  # Provide your OpenAI API key
        )

        # Dictionary to hold analysis results
        analysis_results = {}
        # List files in the repository
        files = chain.ls_files(repo_path)

        # Read and analyze each file
        for file in files:
            content = chain.read_file(file)
            # Example analysis: Code complexity
            complexity_prompt = "Analyze the complexity of this code:\n\n" + content
            complexity_analysis = chain.complete(complexity_prompt)
            analysis_results[file] = complexity_analysis

        return analysis_results

