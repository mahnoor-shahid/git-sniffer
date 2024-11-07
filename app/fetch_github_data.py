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
        self.graphql_url = 'https://api.github.com/graphql'
        self.urls = set()
        self.data_dir = os.path.join(os.getcwd(), 'data')
        self.pr_counts = {}  # Dictionary to store PR count per contributor
        self.commit_counts = {}  # Dictionary to store commit count per contributor
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
        """Fetch commits for each repository and save to a CSV file."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching commits"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                file_name = f"{repo_owner}++{repo_name}.csv"
                commits_filename = os.path.join(self.commits_dir, file_name)
                self.commit_counts[f"{repo_owner}-{repo_name}"] = {}

                # Initialize pagination variables
                has_next_page = True
                end_cursor = None

                # Fetch the default branch of the repository (e.g., main or master)
                default_branch_query = """
                query($owner: String!, $name: String!) {
                    repository(owner: $owner, name: $name) {
                        defaultBranchRef {
                            name
                        }
                    }
                }
                """
                variables = {'owner': repo_owner, 'name': repo_name}
                response = requests.post(
                    'https://api.github.com/graphql',
                    json={'query': default_branch_query, 'variables': variables},
                    headers=self.headers
                )

                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'repository' in data['data']:
                        default_branch = data['data']['repository']['defaultBranchRef']['name']
                        #print(f"Default branch for {repo_name}: {default_branch}") ## Good for debugging
                    else:
                        print(f"Failed to fetch default branch for {repo_name}. Skipping...")
                        continue
                else:
                    print(f"Failed to fetch default branch for {repo_name}. Skipping...")
                    continue

                # GraphQL query to fetch commits from the repository
                commits_query = """
                query($owner: String!, $name: String!, $cursor: String, $branch: String!) {
                    repository(owner: $owner, name: $name) {
                        object(expression: $branch) {
                            ... on Commit {
                                history(first: 100, after: $cursor) {
                                    edges {
                                        node {
                                            oid
                                            author {
                                                name
                                                email
                                                user {
                                                    login
                                                }
                                            }
                                            committedDate
                                            message
                                        }
                                    }
                                    pageInfo {
                                        hasNextPage
                                        endCursor
                                    }
                                }
                            }
                        }
                    }
                }
                """

                # Loop through pages of commits until all commits are fetched
                while has_next_page:
                    variables = {'owner': repo_owner, 'name': repo_name, 'cursor': end_cursor, 'branch': default_branch}
                    response = requests.post(
                        'https://api.github.com/graphql',
                        json={'query': commits_query, 'variables': variables},
                        headers=self.headers
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'repository' in data['data']:
                            repository_object = data['data']['repository']['object']
                            if repository_object and 'history' in repository_object:
                                commits = repository_object['history']['edges']
                                page_info = repository_object['history']['pageInfo']

                                # Update commit counts for contributors
                                for commit in commits:
                                    author_login = commit['node']['author']['user']['login'] if commit['node']['author']['user'] else 'N/A'
                                    author_name = commit['node']['author']['name'] if commit['node']['author'] else 'N/A'
                                    if author_login:
                                        if author_login not in self.commit_counts[f"{repo_owner}-{repo_name}"]:
                                            self.commit_counts[f"{repo_owner}-{repo_name}"][author_login] = 0
                                        self.commit_counts[f"{repo_owner}-{repo_name}"][author_login] += 1
                                    else:
                                        if author_name not in self.commit_counts[f"{repo_owner}-{repo_name}"]:
                                            self.commit_counts[f"{repo_owner}-{repo_name}"][author_name] = 0
                                        self.commit_counts[f"{repo_owner}-{repo_name}"][author_name] += 1
                                


                                # Save commits to CSV file
                                with open(commits_filename, 'a', newline='', encoding='utf-8') as commits_csv:
                                    fieldnames = ['commit_sha', 'commit_author_name', 'commit_author_email', 'commit_message', 'commit_date', 'login']
                                    writer = csv.DictWriter(commits_csv, fieldnames=fieldnames)

                                    if commits_csv.tell() == 0:  # Write header only if it's the first write
                                        writer.writeheader()

                                    for commit in commits:
                                        commit_data = {
                                            'commit_sha': commit['node']['oid'],
                                            'commit_author_name': commit['node']['author']['name'],
                                            'commit_author_email': commit['node']['author']['email'],
                                            'commit_message': commit['node']['message'],
                                            'commit_date': commit['node']['committedDate'],
                                            'login': author_login
                                        }
                                        writer.writerow(commit_data)

                                # Handle pagination: check if there are more commits to fetch
                                has_next_page = page_info['hasNextPage']
                                end_cursor = page_info['endCursor']
                            else:
                                print(f"No commit history found for {repo_name}")
                                break
                        else:
                            print(f"Error: No commit data found for {repo_name}")
                            break
                    else:
                        print(f"Failed to fetch commits for {repo_name}: {response.status_code}")
                        break

    def fetch_releases(self):
        """Fetch detailed information about releases using GitHub GraphQL API."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching releases"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                releases_filename = os.path.join(self.releases_dir, f"{repo_owner}++{repo_name}.csv")

                # Initialize pagination
                has_next_page = True
                end_cursor = None

                with open(releases_filename, 'w', newline='', encoding='utf-8') as releases_csv:
                    release_writer = None

                    while has_next_page:
                        # GraphQL query to fetch releases
                        query = '''
                        {
                            repository(owner: "%s", name: "%s") {
                                releases(first: 100, after: "%s") {
                                    edges {
                                        node {
                                            id
                                            tagName   
                                            name
                                            createdAt
                                            publishedAt
                                            author {
                                                login 
                                                name
                                            }
                                        }
                                    }
                                    pageInfo {
                                        hasNextPage
                                        endCursor
                                    }
                                }
                            }
                        }
                        ''' % (repo_owner, repo_name, end_cursor if end_cursor else "")


                        # Make the request
                        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})

                        if response.status_code == 200:
                            data = response.json()

                            # Handle errors in the response
                            if 'errors' in data:
                                print(f"GraphQL query failed with errors: {data['errors']}")
                                break

                            # Fetch release edges
                            if 'data' in data:
                                release_edges = data['data']['repository']['releases']['edges']
                                page_info = data['data']['repository']['releases']['pageInfo']

                                if not release_writer:
                                    fieldnames = ['id', 'tag_name', 'name', 'created_at', 'published_at',  'author_login', 'author_name']
                                    release_writer = csv.DictWriter(releases_csv, fieldnames=fieldnames)
                                    release_writer.writeheader()

                                # Write releases to CSV
                                for release in release_edges:
                                    release_data = release['node']
                                    # Check if author data exists, if not, set default values
                                    author_login = release_data['author']['login'] if release_data['author'] else 'N/A'
                                    author_name = release_data['author']['name'] if release_data['author'] else 'N/A'

                                    release_data = {
                                        'id': release['node']['id'],
                                        'tag_name': release['node']['tagName'],
                                        'name': release['node']['name'],
                                        'created_at': release['node']['createdAt'],
                                        'published_at': release['node']['publishedAt'],
                                        'author_login': author_login,
                                        'author_name': author_name
                                    }
                                    release_writer.writerow(release_data)

                                # Handle pagination
                                has_next_page = page_info['hasNextPage']
                                end_cursor = page_info['endCursor']
                            else:
                                print(f"Unexpected response structure: {data}")
                                break
                        else:
                            print(f"GraphQL request failed for {repo_name} with status code {response.status_code}")
                            break


    def fetch_pulls(self):
        """Fetch detailed information about pull requests using GitHub GraphQL API."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')
        
        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching pull requests"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                pulls_filename = os.path.join(self.pulls_dir, f"{repo_owner}++{repo_name}.csv")
                self.pr_counts[f"{repo_owner}-{repo_name}"] = {}  # Dictionary to store commit count per contributor

                # Initialize pagination
                has_next_page = True
                end_cursor = None

                with open(pulls_filename, 'w', newline='', encoding='utf-8') as pulls_csv:
                    pull_writer = None

                    while has_next_page:
                        # GraphQL query to fetch pull requests
                        query = '''
                        {
                            repository(owner: "%s", name: "%s") {
                                pullRequests(first: 100, after: "%s") {
                                    edges {
                                        node {
                                            id
                                            title
                                            state
                                            createdAt
                                            updatedAt
                                            closedAt
                                            mergedAt
                                            body
                                            url
                                            author {
                                                login
                                                    ... on User {
                                                    name
                                                }
                                            }
                                        }
                                    }
                                    pageInfo {
                                        hasNextPage
                                        endCursor
                                    }
                                }
                            }
                        }
                        ''' % (repo_owner, repo_name, end_cursor if end_cursor else "")

                        # Make the request
                        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})

                        if response.status_code == 200:
                            data = response.json()

                            # Handle errors
                            if 'errors' in data:
                                print(f"GraphQL query failed with errors: {data['errors']}")
                                break

                            # Fetch pull request edges
                            if 'data' in data:
                                pull_edges = data['data']['repository']['pullRequests']['edges']
                                page_info = data['data']['repository']['pullRequests']['pageInfo']

                                # Update PR counts for contributors
                                for pull in pull_edges:
                                    pr_author_login = pull['node']['author']['login'] if pull['node']['author'] else 'N/A'
                                    pr_author_name = pull['node']['author']['name'] if pull['node']['author'] else 'N/A'
                                    if pr_author_login:
                                        if pr_author_login not in self.pr_counts[f"{repo_owner}-{repo_name}"]:
                                            self.pr_counts[f"{repo_owner}-{repo_name}"][pr_author_login] = 0
                                        self.pr_counts[f"{repo_owner}-{repo_name}"][pr_author_login] += 1
                                    else:
                                        if pr_author_name not in self.pr_counts[f"{repo_owner}-{repo_name}"]:
                                            self.pr_counts[f"{repo_owner}-{repo_name}"][pr_author_name] = 0
                                        self.pr_counts[f"{repo_owner}-{repo_name}"][pr_author_name] += 1                               


                                if not pull_writer:
                                    fieldnames = ['pull_number', 'title', 'state', 'created_at', 'updated_at', 'closed_at', 'merged_at', 'user', 'url']
                                    pull_writer = csv.DictWriter(pulls_csv, fieldnames=fieldnames)
                                    pull_writer.writeheader()

                                # Write pull requests to CSV
                                for pull in pull_edges:
                                    # Check if author data exists, if not, set default values
                                    author_login = pull['node']['author']['login'] if pull['node']['author'] else 'N/A'
                                    #author_name = issue_data['author']['name'] if issue_data['author'] else 'N/A'

                                    pull_data = {
                                        'pull_number': pull['node']['id'],
                                        'title': pull['node']['title'],
                                        'state': pull['node']['state'],
                                        'created_at': pull['node']['createdAt'],
                                        'updated_at': pull['node']['updatedAt'],
                                        'closed_at': pull['node']['closedAt'],
                                        'merged_at': pull['node']['mergedAt'],
                                        'user':author_login,
                                        'url': pull['node']['url']
                                    }
                                    pull_writer.writerow(pull_data)

                                # Handle pagination
                                has_next_page = page_info['hasNextPage']
                                end_cursor = page_info['endCursor']
                            else:
                                print(f"Unexpected response structure: {data}")
                                break
                        else:
                            print(f"GraphQL request failed for {repo_name} with status code {response.status_code}")
                            break


    def fetch_issues(self):
        """Fetch detailed information about issues using GitHub GraphQL API."""
        metadata_file = os.path.join(self.metadata_dir, 'combined_metadata.csv')

        with open(metadata_file, newline='', encoding='utf-8') as metadata_csv:
            reader = csv.DictReader(metadata_csv)

            for row in tqdm(reader, desc="Fetching issues"):
                repo_url = row['html_url']
                repo_owner, repo_name = self._parse_github_url(repo_url)
                issues_filename = os.path.join(self.issues_dir, f"{repo_owner}++{repo_name}.csv")

                # Initialize pagination
                has_next_page = True
                end_cursor = None

                with open(issues_filename, 'w', newline='', encoding='utf-8') as issues_csv:
                    issue_writer = None

                    while has_next_page:
                        # GraphQL query to fetch issues
                        query = '''
                        {
                            repository(owner: "%s", name: "%s") {
                                issues(first: 100, after: "%s") {
                                    edges {
                                        node {
                                            id
                                            title
                                            state
                                            createdAt
                                            updatedAt
                                            closedAt
                                            body
                                            url
                                            author {
                                            login 
                                        }
                                        }
                                    }
                                    pageInfo {
                                        hasNextPage
                                        endCursor
                                    }
                                }
                            }
                        }
                        ''' % (repo_owner, repo_name, end_cursor if end_cursor else "")

                        # Make the request
                        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})

                        if response.status_code == 200:
                            data = response.json()

                            # Handle errors
                            if 'errors' in data:
                                print(f"GraphQL query failed with errors: {data['errors']}")
                                break

                            # Fetch issue edges
                            if 'data' in data:
                                issue_edges = data['data']['repository']['issues']['edges']
                                page_info = data['data']['repository']['issues']['pageInfo']

                                if not issue_writer:
                                    fieldnames = ['id', 'title', 'state', 'created_at', 'updated_at', 'closed_at', 'body', 'user', 'url']
                                    issue_writer = csv.DictWriter(issues_csv, fieldnames=fieldnames)
                                    issue_writer.writeheader()

                                # Write issues to CSV
                                for issue in issue_edges:
                                    # Check if author data exists, if not, set default values
                                    author_login = issue['node']['author']['login'] if issue['node']['author'] else 'N/A'
                                    #author_name = issue_data['author']['name'] if issue_data['author'] else 'N/A'

                                    issue_data = {
                                        'id': issue['node']['id'],
                                        'title': issue['node']['title'],
                                        'state': issue['node']['state'],
                                        'created_at': issue['node']['createdAt'],
                                        'updated_at': issue['node']['updatedAt'],
                                        'closed_at': issue['node']['closedAt'],
                                        'body': issue['node']['body'],
                                        'user': author_login,
                                        #'name':author_name,
                                        'url': issue['node']['url']
                                    }
                                    issue_writer.writerow(issue_data)

                                # Handle pagination
                                has_next_page = page_info['hasNextPage']
                                end_cursor = page_info['endCursor']
                            else:
                                print(f"Unexpected response structure: {data}")
                                break
                        else:
                            print(f"GraphQL request failed for {repo_name} with status code {response.status_code}")
                            break


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

                # Initialize variables for pagination
            has_next_page = True
            end_cursor = None  # To store the cursor for the next page

            # Open the CSV file in append mode to write stargazers incrementally
            with open(stargazers_filename, 'w', newline='', encoding='utf-8') as stargazers_csv:
                stargazer_writer = None  # We'll initialize the writer after the first batch

                while has_next_page:
                    # Update the query to include the endCursor for pagination
                    query = '''
                    {
                        repository(owner: "%s", name: "%s") {
                            stargazers(first: 100, after: "%s") {
                                edges {
                                    node {
                                        login
                                        avatarUrl
                                        url
                                    }
                                    starredAt
                                }
                                pageInfo {
                                    hasNextPage
                                    endCursor
                                }
                            }
                        }
                    }
                    ''' % (repo_owner, repo_name, end_cursor if end_cursor else "")

                    # Make the API request
                    response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})

                    if response.status_code == 200:
                        data = response.json()
                        stargazer_edges = data['data']['repository']['stargazers']['edges']
                        page_info = data['data']['repository']['stargazers']['pageInfo']

                        if not stargazer_edges:
                            print(f"No stargazers found for {repo_name}.")
                            break  # No more stargazers, exit loop

                        # Initialize the CSV writer with fieldnames after fetching the first batch
                        if not stargazer_writer:
                            fieldnames = ['login', 'avatarUrl', 'url', 'starredAt']
                            stargazer_writer = csv.DictWriter(stargazers_csv, fieldnames=fieldnames)
                            stargazer_writer.writeheader()  # Write header only once

                        # Write stargazer data incrementally
                        for stargazer in stargazer_edges:
                            node = stargazer['node']
                            starred_at = stargazer['starredAt']  # Get the starredAt date
                            stargazer_data = {
                                'login': node['login'],
                                'avatarUrl': node['avatarUrl'],
                                'url': node['url'],
                                'starredAt': starred_at
                            }

                            stargazer_writer.writerow(stargazer_data)  # Write to CSV

                        # Update pagination info
                        has_next_page = page_info['hasNextPage']
                        end_cursor = page_info['endCursor']  # Set the cursor for the next page

                        #print(f"Fetched {len(stargazer_edges)} stargazers. {'More pages to fetch' if has_next_page else 'No more pages.'}")
                    else:
                        print(f"GraphQL request failed for {repo_name} with status code {response.status_code}")
                        break  # Exit loop on failure

    def fetch_forks(self):
        """Fetch forks for each repository using GraphQL and save to a CSV file named as owner++reponame_forks.csv."""
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

                # Initialize variables for pagination
                has_next_page = True
                end_cursor = None  # To store the cursor for the next page

                # Open the CSV file in append mode to write forks incrementally
                with open(forks_filename, 'w', newline='', encoding='utf-8') as forks_csv:
                    forks_writer = None  # Initialize writer after first batch

                    while has_next_page:
                        # GraphQL query to fetch forks with pagination
                        query = '''
                        {
                            repository(owner: "%s", name: "%s") {
                                forks(first: 100, after: "%s") {
                                    edges {
                                        node {
                                            id
                                            name
                                            nameWithOwner  # Corrected to nameWithOwner
                                            owner {
                                                login
                                            }
                                            createdAt
                                            updatedAt
                                            url
                                        }
                                    }
                                    pageInfo {
                                        hasNextPage
                                        endCursor
                                    }
                                }
                            }
                        }
                        ''' % (repo_owner, repo_name, end_cursor if end_cursor else "")

                        # Make the GraphQL request
                        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})

                        if response.status_code == 200:
                            data = response.json()
                            fork_edges = data['data']['repository']['forks']['edges']
                            page_info = data['data']['repository']['forks']['pageInfo']

                            if not fork_edges:
                                print(f" No forks found for {repo_name}.")
                                break  # No more forks, exit loop

                            # Initialize the CSV writer with fieldnames after fetching the first batch
                            if not forks_writer:
                                fieldnames = ['fork_id', 'fork_name', 'fork_full_name', 'fork_owner', 'fork_url', 'fork_created_at', 'fork_updated_at']
                                forks_writer = csv.DictWriter(forks_csv, fieldnames=fieldnames)
                                forks_writer.writeheader()  # Write header only once

                            # Write fork data incrementally
                            for fork in fork_edges:
                                node = fork['node']
                                fork_data = {
                                    'fork_id': node['id'],
                                    'fork_name': node['name'],
                                    'fork_full_name': node['nameWithOwner'],
                                    'fork_owner': node['owner']['login'],
                                    'fork_url': node['url'],
                                    'fork_created_at': node['createdAt'],
                                    'fork_updated_at': node['updatedAt']
                                }
                                forks_writer.writerow(fork_data)

                            # Update pagination info
                            has_next_page = page_info['hasNextPage']
                            end_cursor = page_info['endCursor']  # Set the cursor for the next page

                            #print(f"Fetched {len(fork_edges)} forks. {'More pages to fetch' if has_next_page else 'No more pages.'}")
                        else:
                            print(f"GraphQL request failed for {repo_name} with status code {response.status_code}")
                            break  # Exit loop on failure


    def fetch_subscribers(self):
        """Fetch subscribers (watchers) for each repository using GraphQL and save to a CSV file named as owner++reponame_subscribers.csv."""
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

                # Initialize variables for pagination
                has_next_page = True
                end_cursor = None  # To store the cursor for the next page

                # Open the CSV file in append mode to write subscribers incrementally
                with open(subscribers_filename, 'w', newline='', encoding='utf-8') as subscribers_csv:
                    subscribers_writer = None  # Initialize writer after first batch

                    while has_next_page:
                        # GraphQL query to fetch subscribers (watchers) with pagination
                        query = '''
                        {
                            repository(owner: "%s", name: "%s") {
                                watchers(first: 100, after: "%s") {
                                    edges {
                                        node {
                                            login
                                            id
                                            url
                                        }
                                    }
                                    pageInfo {
                                        hasNextPage
                                        endCursor
                                    }
                                }
                            }
                        }
                        ''' % (repo_owner, repo_name, end_cursor if end_cursor else "")

                        # Make the GraphQL request
                        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})

                        if response.status_code == 200:
                            data = response.json()
                            subscriber_edges = data['data']['repository']['watchers']['edges']
                            page_info = data['data']['repository']['watchers']['pageInfo']

                            if not subscriber_edges:
                                print(f" No subscribers found for {repo_name}.")
                                break  # No more subscribers, exit loop

                            # Initialize the CSV writer with fieldnames after fetching the first batch
                            if not subscribers_writer:
                                fieldnames = ['subscriber_login', 'subscriber_id', 'subscriber_url']
                                subscribers_writer = csv.DictWriter(subscribers_csv, fieldnames=fieldnames)
                                subscribers_writer.writeheader()  # Write header only once

                            # Write subscriber data incrementally
                            for subscriber in subscriber_edges:
                                node = subscriber['node']
                                subscriber_data = {
                                    'subscriber_login': node['login'],
                                    'subscriber_id': node['id'],
                                    'subscriber_url': node['url']
                                }
                                subscribers_writer.writerow(subscriber_data)

                            # Update pagination info
                            has_next_page = page_info['hasNextPage']
                            end_cursor = page_info['endCursor']  # Set the cursor for the next page

                            #print(f"Fetched {len(subscriber_edges)} subscribers. {'More pages to fetch' if has_next_page else 'No more pages.'}")
                        else:
                            print(f"GraphQL request failed for {repo_name} with status code {response.status_code}")
                            break  # Exit loop on failure


    def analyze(self, analyze_flag):
        self.analyze_flag = analyze_flag
        if self.analyze_flag:
            print('\nAnalyzing the Github Repositories...')
            generate_summary(src_dir=self.readme_directory, target_dir=self.analysis_directory)
            # extract_topics_from_summaries(target_dir=self.analysis_directory)
