import argparse
import sys
import nltk
import os


from app.fetch_github_data import GitHubRepoFetcher

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Fetch GitHub repositories based on multiple search terms.")
    parser.add_argument('-t', '--token', type=str, required=True, help='GitHub access token')
    parser.add_argument('-s', '--search', nargs='+', required=True, help='Search terms for repositories, e.g., -s term1 term2')
    parser.add_argument('-m', '--max_repos', type=int, default=10, help='Maximum number of repositories to fetch per term')
    parser.add_argument('-r', '--readme', type=bool, default=False, help='True or 1 if README files are needed else False or 0')
    parser.add_argument('-a', '--analyze', type=bool, default=False, help='True or 1 if analysis is needed else False or 0')

    args = parser.parse_args()
    #nltk.data.path.extend([os.path.join(sys.prefix, 'nltk_data'), 
    #                      os.path.join(sys.prefix, 'Lib', 'nltk_data'),
    #                      os.path.join(sys.prefix, 'lib', 'nltk_data')])
    
    if args.analyze and not args.readme:
        print("\nREADME files will be stored on your local system as part of the analysis.")
        user_input = input("Do you want to proceed with fetching README files? (y/n): ").strip().lower()
        if user_input.lower() == 'y' or user_input.lower() == 'yes':
            args.readme = True
            # Ensure you have the required NLTK resources
            print("\nDownloading a few necessary packages used for analysis...")
            try:
                nltk.download('punkt')
                nltk.download('punkt_tab')
                nltk.download('stopwords')
            except Exception as e:
                print(f"Error downloading NLTK data: {e}")
                raise
        else:
            print("Exiting: README files are required for analysis.")
            sys.exit(1)

    fetcher = GitHubRepoFetcher(args.token)
    fetcher.fetch_repos(args.search, args.max_repos)

    print(f"Number of URLs loaded: {len(fetcher.urls)}")
    # fetcher.clone_repositories()
    # fetcher.fetch_stargazers()
    # fetcher.fetch_forks()
    # fetcher.fetch_subscribers()
    # fetcher.fetch_releases()
    # fetcher.fetch_issues()
    # fetcher.fetch_pulls()
    # fetcher.fetch_commits()
    fetcher.fetch_contributors()
    # fetcher.fetch_readme(args.readme)
    # fetcher.clone_repositories()
    print(f"Number of Repositories Processed: {len(fetcher.urls)}")
    fetcher.analyze(args.analyze)

