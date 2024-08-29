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


def get_commit_messages(previous_tag):
    """Get commit messages between the last release tag and the current HEAD."""
    if previous_tag == "0.0.0":
        print("This is the first release, no comparison necessary.")
        return ["Initial release."]

    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    compare_url = f"{GITHUB_API_URL}/compare/{previous_tag}...main"

    response = requests.get(compare_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch comparison: {response.status_code}")

    comparison = response.json()
    commits = comparison['commits']

    commit_messages = [f"{commit['commit']['message']} by {commit['commit']['author']['name']} in {commit['sha'][:7]}" for commit in commits]

    return commit_messages


def generate_release_body(commit_messages, manual_message=None):
    """Generate the release body from commit messages and manual input."""
    body = "### What's Changed\n\n"
    for commit in commit_messages:
        commit_message = commit['message']
        author_login = commit['author_login']
        commit_url = commit['commit_url']

        # Format each commit entry with message, author, and commit URL
        body += f"- {commit_message} by [{author_login}]({commit_url})\n"

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
