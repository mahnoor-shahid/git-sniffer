
if __name__ == '__main__':
    token = 'YOUR_GITHUB_TOKEN'  # Replace with your actual GitHub token
    search_term = 'genome'
    max_repos = 200
    
    fetcher = GitHubRepoFetcher(token)
    urls = fetcher.fetch_repos(search_term, max_repos)
    print(f"Number of URLs loaded: {len(urls)}")
