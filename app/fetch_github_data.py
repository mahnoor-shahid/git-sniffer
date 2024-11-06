import requests
from tqdm import tqdm
import os
import pandas as pd
import subprocess
import csv
from app.process_metadata import structure_metadata
from app.text_segments_transformers import generate_summary, extract_topics_from_summaries

class GitHubRepoFetcher:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com/search/repositories"
        self.headers = {'Authorization': f'token {self.token}'}
        self.urls = set()
        self.data_dir = os.path.join(os.getcwd(), 'data')
        
        self.metadata_dir = os.path.join(self.data_dir, 'metadata')
        self.contributors_dir = os.path.join(self.data_dir, 'contributors')
        self.commits_dir = os.path.join(self.data_dir, 'commits')
        self.issues_dir = os.path.join(self.data_dir, 'issues')
        self.pulls_dir = os.path.join(self.data_dir, 'pulls')
        self.releases_dir = os.path.join(self.data_dir, 'releases')
        self.stargazers_dir = os.path.join(self.data_dir, 'stars')
        self.forks_dir = os.path.join(self.data_dir, 'forks')
        self.subscribers_dir = os.path.join(self.data_dir, 'subscribers')
        self.readme_directory = os.path.join(self.data_dir, 'readme')
        self.analysis_directory = os.path.join(self.data_dir, 'analysis')

        if not self.validate_token():
            raise ValueError("\nInvalid GitHub token provided.")  # Raise an error to indicate invalid token

        # Ensure directories exist
        for dir_path in [self.metadata_dir, self.contributors_dir, self.commits_dir, 
                         self.issues_dir, self.pulls_dir, self.releases_dir, 
                         self.readme_directory, self.analysis_directory]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
    def validate_token(self):
        """ Check if the provided token is valid by making a request to the /user endpoint. """
        try:
            response = requests.get('https://api.github.com/user', headers=self.headers)
            if response.status_code == 200:
                print("\nToken is valid.")
                return True
            elif response.status_code == 401:
                print("\nInvalid token.")
                return False
            else:
                print(f"\nFailed to validate token: {response.status_code}")
                return False
        except Exception as e:
            print(f"\nError during token validation: {e}")
            return False

    def fetch_repos(self, search_terms, max_repos):
        combined_csv_filename = os.path.join(self.metadata_dir, 'combined_metadata.csv')
    
        if os.path.isfile(combined_csv_filename):
            # Prompt the user for confirmation to delete the existing file
            confirm = input(f"The file '{combined_csv_filename}' already exists. Do you want to delete it? (y/n): ").strip().lower()
            if confirm == 'y':
                os.remove(combined_csv_filename)
                print(f"Deleted the existing file: {combined_csv_filename}")
            else:
                print(f"Keeping the existing file: {combined_csv_filename}")

        # Proceed with fetching repositories
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
                pbar = tqdm(desc=f"Fetching metadata for search term '{term}'", unit="url")

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
        repos_directory = os.path.join(self.data_dir, 'repos')
        if not os.path.exists(repos_directory):
            os.makedirs(repos_directory)
        for url in self.urls:
            repo_name = url.split('/')[-1]
            repo_path = os.path.join(repos_directory, repo_name)
            if not os.path.exists(repo_path):
                subprocess.run(['git', 'clone', url, repo_path])

    def fetch_contributors(self):
        """Fetch contributors for each repository and save to a CSV file named as owner++reponame.csv."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching contributors"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                file_name = f"{repo_owner}++{repo_name}.csv"
                contributors_filename = os.path.join(self.contributors_dir, file_name)

                contributors_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contributors"
                contributors = []
                page = 1

                while True:
                    response = requests.get(contributors_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_contributors = response.json()

                        if not page_contributors:
                            break  # No more contributors, exit loop
                        
                        contributors.extend(page_contributors)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch contributors for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Open the CSV file to write the contributors' data
                with open(contributors_filename, 'w', newline='', encoding='utf-8') as contributors_csv:
                    if contributors:
                        fieldnames = ['repo_owner', 'repo_name', 'contributor_login', 'contributions'] + list(contributors[0].keys())
                        writer = csv.DictWriter(contributors_csv, fieldnames=fieldnames)
                        writer.writeheader()

                        for contributor in contributors:
                            contributor_data = {
                                'repo_owner': repo_owner,
                                'repo_name': repo_name,
                                'contributor_login': contributor.get('login'),
                                'contributions': contributor.get('contributions')
                            }
                            contributor_data.update(contributor)
                            writer.writerow(contributor_data)
                    else:
                        print(f"No contributors found for {repo_name}")

    def fetch_commits(self):
        """Fetch commits for each repository and save to a CSV file named as owner++reponame.csv."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching commits"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                file_name = f"{repo_owner}++{repo_name}.csv"
                commits_filename = os.path.join(self.commits_dir, file_name)

                commits_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
                commits = []
                page = 1

                while True:
                    response = requests.get(commits_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_commits = response.json()

                        if not page_commits:
                            break  # No more commits, exit loop
                        
                        commits.extend(page_commits)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch commits for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Open the CSV file to write the commits' data
                with open(commits_filename, 'w', newline='', encoding='utf-8') as commits_csv:
                    if commits:
                        fieldnames = ['repo_owner', 'repo_name', 'commit_sha', 'commit_author', 'commit_message', 'commit_date'] + list(commits[0].keys())
                        writer = csv.DictWriter(commits_csv, fieldnames=fieldnames)
                        writer.writeheader()

                        for commit in commits:
                            commit_data = {
                                'repo_owner': repo_owner,
                                'repo_name': repo_name,
                                'commit_sha': commit.get('sha'),
                                'commit_author': commit['commit']['author'].get('name'),
                                'commit_message': commit['commit'].get('message'),
                                'commit_date': commit['commit']['author'].get('date')
                            }
                            commit_data.update(commit)
                            writer.writerow(commit_data)
                    else:
                        print(f"No commits found for {repo_name}")


    def fetch_releases(self):
        """Fetch detailed information about releases in the repositories."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')
        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)
            for row in tqdm(reader, desc="Fetching releases"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                releases_filename = os.path.join(self.releases_dir, f"{repo_owner}++{repo_name}.csv")
                releases_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
                releases = []
                page = 1

                while True:
                    response = requests.get(releases_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_releases = response.json()

                        if not page_releases:
                            break  # No more releases, exit loop
                        
                        releases.extend(page_releases)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch releases for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Open the CSV file to write the releases' data
                with open(releases_filename, 'w', newline='', encoding='utf-8') as releases_csv:
                    if releases:
                        # Define fieldnames based on expected keys
                        fieldnames = ['id', 'tag_name', 'name', 'created_at', 'published_at', 'body', 'html_url']
                        writer = csv.DictWriter(releases_csv, fieldnames=fieldnames)
                        writer.writeheader()

                        for release in releases:
                            # Create a dictionary with only the relevant fields
                            release_data = {
                                'id': release.get('id', ''),
                                'tag_name': release.get('tag_name', ''),
                                'name': release.get('name', ''),
                                'created_at': release.get('created_at', ''),
                                'published_at': release.get('published_at', ''),
                                'body': release.get('body', ''),
                                'html_url': release.get('html_url', '')
                            }
                            # Write only the data that matches the fieldnames
                            writer.writerow(release_data)
                    else:
                        print(f"No releases found for {repo_name}")



    def fetch_pulls(self):
        """Fetch detailed information about pull requests in the repositories."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching pull requests"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                pulls_filename = f"{repo_owner}++{repo_name}.csv"
                pulls_filepath = os.path.join(self.pulls_dir, pulls_filename)

                pulls_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
                pulls_data = []
                page = 1

                while True:
                    response = requests.get(pulls_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_pulls = response.json()

                        if not page_pulls:
                            break  # No more pull requests, exit loop
                        
                        pulls_data.extend(page_pulls)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch pull requests for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Open the CSV file to write the pulls' data
                with open(pulls_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    if pulls_data:
                        fieldnames = ['pull_number', 'title', 'state', 'created_at', 'updated_at', 'closed_at', 'merged_at', 'user', 'html_url'] + list(pulls_data[0].keys())
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()

                        for pull in pulls_data:
                            pull_data = {
                                'pull_number': pull['number'],
                                'title': pull['title'],
                                'state': pull['state'],
                                'created_at': pull['created_at'],
                                'updated_at': pull.get('updated_at', ''),
                                'closed_at': pull.get('closed_at', ''),
                                'merged_at': pull.get('merged_at', ''),
                                'user': pull['user']['login'],
                                'html_url': pull['html_url']
                            }
                            pull_data.update(pull)
                            writer.writerow(pull_data)
                    else:
                        print(f"No pull requests found for {repo_name}")


    def fetch_issues(self):
        """Fetch detailed information about issues in the repositories."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching issues"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                issues_filename = f"{repo_owner}++{repo_name}.csv"
                issues_filepath = os.path.join(self.issues_dir, issues_filename)

                issues_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
                issues_data = []
                page = 1

                while True:
                    response = requests.get(issues_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_issues = response.json()

                        if not page_issues:
                            break  # No more issues, exit loop
                        
                        issues_data.extend(page_issues)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch issues for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Define fieldnames based on all keys present in issue data
                fieldnames = [
                    'url', 'repository_url', 'labels_url', 'comments_url', 'events_url',
                    'html_url', 'id', 'node_id', 'number', 'title', 'user', 'labels',
                    'state', 'locked', 'assignee', 'assignees', 'milestone', 'comments',
                    'created_at', 'updated_at', 'closed_at', 'author_association',
                    'active_lock_reason', 'body', 'reactions', 'timeline_url',
                    'performed_via_github_app', 'state_reason'
                ]

                # Open the CSV file to write the issues' data
                with open(issues_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    if issues_data:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()

                        for issue in issues_data:
                            # Prepare issue_data with all fields, use get() for optional fields
                            issue_data = {
                                'url': issue.get('url', ''),
                                'repository_url': issue.get('repository_url', ''),
                                'labels_url': issue.get('labels_url', ''),
                                'comments_url': issue.get('comments_url', ''),
                                'events_url': issue.get('events_url', ''),
                                'html_url': issue.get('html_url', ''),
                                'id': issue.get('id', ''),
                                'node_id': issue.get('node_id', ''),
                                'number': issue.get('number', ''),
                                'title': issue.get('title', ''),
                                'user': issue.get('user', ''),
                                'labels': issue.get('labels', ''),
                                'state': issue.get('state', ''),
                                'locked': issue.get('locked', ''),
                                'assignee': issue.get('assignee', ''),
                                'assignees': issue.get('assignees', ''),
                                'milestone': issue.get('milestone', ''),
                                'comments': issue.get('comments', ''),
                                'created_at': issue.get('created_at', ''),
                                'updated_at': issue.get('updated_at', ''),
                                'closed_at': issue.get('closed_at', ''),
                                'author_association': issue.get('author_association', ''),
                                'active_lock_reason': issue.get('active_lock_reason', ''),
                                'body': issue.get('body', ''),
                                'reactions': issue.get('reactions', ''),
                                'timeline_url': issue.get('timeline_url', ''),
                                'performed_via_github_app': issue.get('performed_via_github_app', ''),
                                'state_reason': issue.get('state_reason', '')
                            }
                            writer.writerow(issue_data)
                    else:
                        print(f"No issues found for {repo_name}")


    def fetch_stargazers(self):
        """Fetch stargazers for each repository and save to a CSV file named as owner++reponame.csv."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching stargazers"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                file_name = f"{repo_owner}++{repo_name}.csv"
                stargazers_filename = os.path.join(self.stargazers_dir, file_name)

                # Ensure the directory exists
                os.makedirs(self.stargazers_dir, exist_ok=True)

                stargazers_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/stargazers"
                stargazers = []
                page = 1

                while True:
                    response = requests.get(stargazers_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_stargazers = response.json()

                        if not page_stargazers:
                            break  # No more stargazers, exit loop
                        
                        stargazers.extend(page_stargazers)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch stargazers for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Open the CSV file to write the stargazers' data
                with open(stargazers_filename, 'w', newline='', encoding='utf-8') as stargazers_csv:
                    if stargazers:
                        # Define fieldnames based on expected keys
                        fieldnames = ['login', 'id', 'node_id', 'avatar_url', 'url', 'html_url', 'type']
                        writer = csv.DictWriter(stargazers_csv, fieldnames=fieldnames)
                        writer.writeheader()

                        for stargazer in stargazers:
                            # Create a dictionary with only the relevant fields
                            stargazer_data = {
                                'login': stargazer.get('login', ''),
                                'id': stargazer.get('id', ''),
                                'node_id': stargazer.get('node_id', ''),
                                'avatar_url': stargazer.get('avatar_url', ''),
                                'url': stargazer.get('url', ''),
                                'html_url': stargazer.get('html_url', ''),
                                'type': stargazer.get('type', '')
                            }
                            # Write only the data that matches the fieldnames
                            writer.writerow(stargazer_data)
                    else:
                        print(f"No stargazers found for {repo_name}")

    def fetch_forks(self):
        """Fetch forks for each repository and save to a CSV file named as owner++reponame_forks.csv."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching forks"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                file_name = f"{repo_owner}++{repo_name}.csv"
                forks_filename = os.path.join(self.forks_dir, file_name)

                # Ensure the directory exists
                os.makedirs(self.forks_dir, exist_ok=True)

                forks_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/forks"
                forks = []
                page = 1

                while True:
                    response = requests.get(forks_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_forks = response.json()

                        if not page_forks:
                            break  # No more forks, exit loop
                        
                        forks.extend(page_forks)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch forks for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Open the CSV file to write the forks' data
                with open(forks_filename, 'w', newline='', encoding='utf-8') as forks_csv:
                    if forks:
                        fieldnames = ['repo_owner', 'repo_name', 'fork_id', 'fork_name', 'fork_full_name', 'fork_owner', 'fork_url', 'fork_created_at', 'fork_updated_at']
                        writer = csv.DictWriter(forks_csv, fieldnames=fieldnames)
                        writer.writeheader()

                        for fork in forks:
                            fork_data = {
                                'repo_owner': repo_owner,
                                'repo_name': repo_name,
                                'fork_id': fork.get('id'),
                                'fork_name': fork.get('name'),
                                'fork_full_name': fork.get('full_name'),
                                'fork_owner': fork.get('owner', {}).get('login', ''),  # owner is a dict
                                'fork_url': fork.get('html_url'),
                                'fork_created_at': fork.get('created_at'),
                                'fork_updated_at': fork.get('updated_at')
                            }
                            writer.writerow(fork_data)
                    else:
                        print(f"No forks found for {repo_name}")

    def fetch_subscribers(self):
        """Fetch subscribers (watchers) for each repository and save to a CSV file named as owner++reponame_subscribers.csv."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching subscribers"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                file_name = f"{repo_owner}++{repo_name}.csv"
                subscribers_filename = os.path.join(self.subscribers_dir, file_name)

                # Ensure the directory exists
                os.makedirs(self.subscribers_dir, exist_ok=True)

                subscribers_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/subscribers"
                subscribers = []
                page = 1

                while True:
                    response = requests.get(subscribers_api_url, headers=self.headers, params={'page': page, 'per_page': 100})
                    
                    if response.status_code == 200:
                        page_subscribers = response.json()

                        if not page_subscribers:
                            break  # No more subscribers, exit loop
                        
                        subscribers.extend(page_subscribers)
                        page += 1  # Move to the next page
                    else:
                        print(f"Failed to fetch subscribers for {repo_name}: {response.status_code}")
                        break  # Exit loop on failure
                
                # Open the CSV file to write the subscribers' data
                with open(subscribers_filename, 'w', newline='', encoding='utf-8') as subscribers_csv:
                    if subscribers:
                        fieldnames = ['repo_owner', 'repo_name', 'subscriber_login', 'subscriber_id', 'subscriber_url']
                        writer = csv.DictWriter(subscribers_csv, fieldnames=fieldnames)
                        writer.writeheader()

                        for subscriber in subscribers:
                            subscriber_data = {
                                'repo_owner': repo_owner,
                                'repo_name': repo_name,
                                'subscriber_login': subscriber.get('login'),
                                'subscriber_id': subscriber.get('id'),
                                'subscriber_url': subscriber.get('html_url')
                            }
                            writer.writerow(subscriber_data)
                    else:
                        print(f"No subscribers found for {repo_name}")

    def analyze(self, analyze_flag):
        self.analyze_flag = analyze_flag
        if self.analyze_flag:
            print('\nAnalyzing the Github Repositories...')
            generate_summary(src_dir=self.readme_directory, target_dir=self.analysis_directory)
            # extract_topics_from_summaries(target_dir=self.analysis_directory)
