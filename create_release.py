import requests
import os
import re

# Replace with your repo and owner
GITHUB_OWNER = "ADORSYS-GIS"
GITHUB_REPO = "wazuh"
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

    # If no releases or tags are found, return a default value
    return "0.0.0"


def increment_version(version):
    """Increment the patch version number."""
    # Remove the 'v' prefix if it exists
    if version.startswith('v'):
        version = version[1:]

    # Match the semantic versioning pattern
    match = re.match(SEMVER_PATTERN, version)
    if not match:
        raise ValueError(f"Invalid semantic version: {version}")

    major, minor, patch = map(int, match.groups())
    patch += 1  # Increment the patch version

    # If the version was "0.0.0", return "0.0.1"
    if version == "0.0.0":
        return "0.0.1"

    return f"{major}.{minor}.{patch}"


def get_commit_messages(since_tag):
    """Get commit messages since the last release or tag."""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    params = {'sha': 'main', 'since': since_tag}
    response = requests.get(COMMITS_URL, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch commits: {response.status_code}")

    commits = response.json()
    commit_messages = [commit['commit']['message'] for commit in commits]
    return commit_messages


def generate_release_body(commit_messages, manual_message=None):
    """Generate the release body from commit messages and manual input."""
    body = "### Changes in this release:\n\n"
    for message in commit_messages:
        body += f"- {message}\n"

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
        print(f"Latest version: {latest_version}")

        new_version = increment_version(latest_version)
        print(f"New version: {new_version}")

        commit_messages = get_commit_messages(latest_version)

        # Check if 'add_description' is set as an environment variable
        add_description = os.getenv("ADD_DESCRIPTION", None)

        if add_description:
            release_body = generate_release_body(commit_messages, add_description)
        else:
            manual_message = input("Enter any additional release notes (optional): ")
            release_body = generate_release_body(commit_messages, manual_message)

        print(f"Generated release notes:\n{release_body}")

        create_release(new_version, release_body)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
