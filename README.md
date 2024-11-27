
# **Git Sniffer**

**Git Sniffer** is a Python package designed to fetch, analyze, and explore GitHub repository data with ease. Leveraging the power of GitHub's GraphQL API, Git Sniffer simplifies the process of retrieving critical repository insights, contributors' activity, and workflows for developers and researchers.

---

## **Features**
- Fetch repository data with keywords or topics.
- Retrieve contributors, commits, issues, pull requests, and more.
- Analyze repository insights, including README files.
- Easy-to-use interface for seamless integration into your projects.

---

## **Installation**

You can install **Git Sniffer** directly from PyPI using pip:

```bash
pip install git-sniffer
```

## **Quick Start Guide**

### **1. Set Up Your GitHub Access Token**

To use **Git Sniffer**, you'll need a personal access token from GitHub.  
Follow these steps to create one:

1. Go to your [GitHub Settings](https://github.com/settings/tokens).
2. Generate a new token with the required permissions (read-only access is sufficient).
3. Copy the token to use with **Git Sniffer**.

### **2. Import and Initialize Git Sniffer**

```python
from git_sniffer import GitHubRepoFetcher

# Initialize with your GitHub token
fetcher = GitHubRepoFetcher(token="your_personal_access_token")
```
### **3. Fetch Repositories by Search Terms**

```python
# Fetch repositories based on search terms
repositories = fetcher.fetch_repos(search_terms=["machine learning", "neuro-symbolic AI"], max_repos=5)
print(f"Fetched {len(repositories)} repositories!")
```

### **4. Fetch Popularity Metrics**

```python
# Fetch stargazers (users who starred the repositories)
fetcher.fetch_stargazers()

# Fetch forks of the repositories
fetcher.fetch_forks()

# Fetch subscribers (watchers) of the repositories
fetcher.fetch_subscribers()
```

### **5. Fetch Repository Details**

```python
# Fetch contributors to the repositories
fetcher.fetch_contributors()

# Fetch commit histories of the repositories
fetcher.fetch_commits()
```

### **6. Fetch Additional Repository Insights**
```python
# Fetch release information
fetcher.fetch_releases()

# Fetch issues in the repositories
fetcher.fetch_issues()

# Fetch pull requests
fetcher.fetch_pulls()
````

## **Advanced Features**

- **Custom GraphQL Queries**: Define and execute your own GraphQL queries to fetch tailored data.
- **Workflow Data Collection**: Extract GitHub Actions workflows from repositories.
- **README Analysis**: Perform text analysis on repository README files using built-in NLP tools.

---

## **Documentation**

Comprehensive documentation is available [here](#) (replace with actual link). It includes detailed instructions, API references, and advanced use cases.

---

## **Contributing**

We welcome contributions to improve Git Sniffer! If you'd like to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description.

---

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## **Support**

If you encounter any issues or have questions, feel free to open an issue on GitHub or contact us directly.


