
import argparse
from app.fetch_repos import GitHubRepoFetcher

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Fetch GitHub repositories based on multiple search terms.")
    parser.add_argument('-t', '--token', type=str, required=True, help='GitHub access token')
    parser.add_argument('-s', '--search', nargs='+', required=True, help='Search terms for repositories, e.g., -s term1 term2')
    parser.add_argument('-m', '--max_repos', type=int, default=100, help='Maximum number of repositories to fetch per term')

    args = parser.parse_args()

    fetcher = GitHubRepoFetcher(args.token)
    fetcher.fetch_repos(args.search, args.max_repos)
    print(f"Number of URLs loaded: {len(fetcher.urls)}")
    fetcher.clone_repositories()
