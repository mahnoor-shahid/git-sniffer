<!-- ![GitHub](https://img.shields.io/github/license/mahnoor-shahid/git-sniffer?style=for-the-badge) -->
<!-- ![GitHub Repo stars](https://img.shields.io/github/stars/mahnoor-shahid/git-sniffer?style=for-the-badge) -->
<!-- ![GitHub forks](https://img.shields.io/github/forks/mahnoor-shahid/git-sniffer?style=for-the-badge) -->
<!-- ![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/mahnoor-shahid/git-sniffer?include_prereleases&style=for-the-badge) -->
<!-- ![GitHub issues](https://img.shields.io/github/issues-raw/mahnoor-shahid/git-sniffer?style=for-the-badge) -->
<!-- ![GitHub pull requests](https://img.shields.io/github/issues-pr/mahnoor-shahid/git-sniffer?style=for-the-badge) -->

![GitHub](https://img.shields.io/github/license/mahnoor-shahid/git-sniffer)
![GitHub Repo stars](https://img.shields.io/github/stars/mahnoor-shahid/git-sniffer)
![GitHub forks](https://img.shields.io/github/forks/mahnoor-shahid/git-sniffer)
![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/mahnoor-shahid/git-sniffer?include_prereleases)
<a href="https://github.com/mahnoor-shahid/git-sniffer" alt="python">
        <img src="https://img.shields.io/badge/python-v3.9-brightgreen" /></a>
<a href="https://github.com/mahnoor-shahid/git-sniffer" alt="numpy">
        <img src="https://img.shields.io/badge/numpy-1.20.3-yellowgreen" /></a>
<a href="https://github.com/mahnoor-shahid/git-sniffer" alt="pandas">
        <img src="https://img.shields.io/badge/pandas-1.2.4-yellowgreen" /></a>
<a href="https://github.com/mahnoor-shahid/git-sniffer" alt="dask">
        <img src="https://img.shields.io/badge/dask-2022.05.02-red" /></a>  <a href="https://github.com/mahnoor-shahid/git-sniffer" alt="scikit-learn">
        <img src="https://img.shields.io/badge/scikit--learn-1.2.1-yellowgreen" /></a>

<!-- ![GitHub issues](https://img.shields.io/github/issues-raw/mahnoor-shahid/git-sniffer) -->
<!--![GitHub pull requests](https://img.shields.io/github/issues-pr/mahnoor-shahid/git-sniffer) -->

# **git-sniffer: a lightweight python package for fetching and analyzing github data**

> **Git Sniffer** is a user-friendly python package designed to simplify GitHub data collection and streamline the process of retrieving critical repository insights, using the powerful GraphQL API. It supports fetching repositories, stars, forks, contributors, commits, and more to explore GitHub activity of selected repositories and analyze with ease. Git Sniffer ensures precise and flexible querying, making it ideal for developers, researchers, and data analysts looking to gain insights into open-source projects and workflows.
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


