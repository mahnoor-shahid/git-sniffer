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
    # parser.add_argument('-r', '--readme', type=bool, default=False, help='True or 1 if README files are needed else False or 0')
    parser.add_argument('-a', '--analyze', type=bool, default=False, help='True or 1 if analysis is needed else False or 0')
    local_flag = False
    args = parser.parse_args()
    #nltk.data.path.extend([os.path.join(sys.prefix, 'nltk_data'), 
    #                      os.path.join(sys.prefix, 'Lib', 'nltk_data'),
    #                      os.path.join(sys.prefix, 'lib', 'nltk_data')])
    
    if args.analyze:
        print("\nFor thorough analysis repositories will be cloned in the local system.")
        user_input = input("Do you want to proceed with fetching the repositories? (y/n): ").strip().lower()
        if user_input.lower() == 'y' or user_input.lower() == 'yes':
            local_flag = True
            # args.readme = True
            # Ensure you have the required NLTK resources
            # print("\nDownloading a few necessary packages used for analysis...")
            # try:
            #     nltk.download('punkt')
            #     nltk.download('punkt_tab')
            #     nltk.download('stopwords')
            # except Exception as e:
            #     print(f"Error downloading NLTK data: {e}")
            #     raise
        else:
            # print("Exiting: README files are required for analysis.")
            sys.exit(1)

    fetcher = GitHubRepoFetcher(args.token)
    fetcher.fetch_repos(args.search, args.max_repos)
    fetcher.fetch_stargazers()
    fetcher.fetch_forks()
    fetcher.fetch_subscribers()
    fetcher.fetch_contributors()
    fetcher.fetch_commits()
    fetcher.fetch_releases()
    fetcher.fetch_issues()
    fetcher.fetch_pulls()
    # fetcher.fetch_readme(args.readme)
    
    if local_flag == True:
        fetcher.clone_repositories()
    print(f"Number of Repositories Processed: {len(fetcher.urls)}")
    # fetcher.analyze(args.analyze)





