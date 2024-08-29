import requests
import os
import re

# Replace with your repo and owner
GITHUB_OWNER = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("REPO_NAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub API URLs
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
RELEASES_URL = f"{GITHUB_API_URL}/releases"
TAGS_URL = f"{GITHUB_API_URL}/tags"
COMMITS_URL = f"{GITHUB_API_URL}/commits"

# Semantic versioning regex pattern
SEMVER_PATTERN = r"^(\d+)\.(\d+)\.(\d+)$"


def get_latest_release():
    """Get the latest release or tag from GitHub."""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}

    # First, try to fetch the latest release
    response = requests.get(RELEASES_URL, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch releases: {response.status_code}")

    releases = response.json()
    if releases:
        latest_release = releases[0]["tag_name"]
        return latest_release

    # If no releases are found, try to fetch the latest tag
    response = requests.get(TAGS_URL, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch tags: {response.status_code}")

    tags = response.json()
    if tags:
        latest_tag = tags[0]["name"]
        return latest_tag

    # If no releases or tags are found, return None to indicate no previous versions
    return None


# If no releases or tags are found, consider this as the first release
latest_version = get_latest_release()
if not latest_version:
    print("No previous releases or tags found.")
    latest_version = "0.0.0"  # Consider this the first release


def increment_version(version, increment_type="patch"):
    """Increment the version number based on the increment type."""
    # Remove the 'v' prefix if it exists
    if version.startswith('v'):
        version = version[1:]

    # Match the semantic versioning pattern
    match = re.match(SEMVER_PATTERN, version)
    if not match:
        raise ValueError(f"Invalid semantic version: {version}")

    major, minor, patch = map(int, match.groups())

    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
    else:  # Default to patch
        patch += 1

    return f"{major}.{minor}.{patch}"


def get_commit_messages(since_tag):
    """Get detailed commit messages since the last release or tag."""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    params = {'sha': 'main', 'since': since_tag}
    response = requests.get(COMMITS_URL, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch commits: {response.status_code}")

    commits = response.json()  # Get full commit details

    return commits


def generate_release_body(commits, manual_message=None):
    """Generate a more detailed release body from commit messages and manual input."""

    # Start with a header
    body = "### What's Changed\n\n"

    # Iterate over the commits and format them
    for commit in commits:
        author = commit['commit']['author']['name']
        message = commit['commit']['message']
        sha = commit['sha'][:7]  # Shortened commit hash
        url = commit['html_url']

        # Add each commit message with the author and a link to the commit
        body += f"- {message} ([{sha}]({url})) by **{author}**\n"

    # Append any additional notes
    if manual_message:
        body += f"\n### Additional Notes:\n{manual_message}\n"

    return body


def create_release(new_version, release_body):
    """Create a new release on GitHub."""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {
        "tag_name": new_version,
        "target_commitish": "main",
        "name": f"Release {new_version}",
        "body": release_body,
        "draft": False,
        "prerelease": False
    }

    response = requests.post(RELEASES_URL, json=data, headers=headers)
    if response.status_code != 201:
        raise Exception(f"Failed to create release: {response.status_code}")

    print(f"Release {new_version} created successfully!")


def main():
    try:
        latest_version = get_latest_release()
        if latest_version is None:
            print("No previous releases or tags found.")
            latest_version = "0.0.0"  # Consider this as the first release

        print(f"Latest version: {latest_version}")

        # Set the output for GitHub Actions
        print(f"::set-output name=latest_version::{latest_version}")
        # Alternatively, use GITHUB_ENV for the latest GitHub Actions format
        with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
            env_file.write(f"latest_version={latest_version}\n")

        # Check if 'INCREMENT_TYPE' is set as an environment variable
        increment_type = os.getenv("INCREMENT_TYPE", "patch").strip().lower()
        print(f"Using increment type: {increment_type}")

        new_version = increment_version(latest_version, increment_type)
        print(f"New version: {new_version}")

        # Set the output for new_version as well
        print(f"::set-output name=new_version::{new_version}")
        # Alternatively, use GITHUB_ENV
        with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
            env_file.write(f"new_version={new_version}\n")

        # Fetch commits since the last release
        commit_messages = get_commit_messages(latest_version)

        # Check if 'ADD_DESCRIPTION' is set as an environment variable
        add_description = os.getenv("ADD_DESCRIPTION", None)

        if add_description:
            release_body = generate_release_body(commit_messages, add_description)
        else:
            release_body = generate_release_body(commit_messages)

        print(f"Generated release notes:\n{release_body}")

        create_release(new_version, release_body)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
