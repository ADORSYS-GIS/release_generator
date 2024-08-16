# GitHub Action: Release Generator

![Release Generator](https://img.shields.io/badge/GitHub%20Action-Release%20Generator-blue)

This GitHub Action automates the process of generating releases in your GitHub repository. It creates a new release based on the latest version tag, increments the version number following semantic versioning, and includes commit messages in the release notes. You can also add a custom description to the release.

## Features

- **Automatic Versioning:** Increments the patch version automatically following semantic versioning.
- **Commit-Based Changelog:** Generates release notes based on commit messages since the last release.
- **Custom Release Description:** Allows for additional custom release notes to be included.
- **Fully Dockerized:** Runs in a Docker container with a Python environment.

## Inputs

| Input Name         | Description                                                               | Required | Default Value |
|--------------------|---------------------------------------------------------------------------|----------|---------------|
| `github_token`     | GitHub token used for authentication with the GitHub API.                 | Yes      | N/A           |
| `add_description`  | Additional custom description for the release.                           | No       | N/A           |

## Outputs

This action does not produce any outputs.

## Example Usage

Here’s an example of how to use this GitHub Action in a workflow:

```yaml
name: Release Workflow

on:
  push:
    branches:
      - main

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Generate Release
        uses: ADORSYS-GIS/release_generator@v1.0.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          add_description: "This is an additional note for the release."
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_USERNAME: ${{ secrets.GITHUB_USERNAME }}
          REPO_NAME: ${{ secrets.REPO_NAME }}
```

## How It Works

1. **Versioning:** The action fetches the latest release or tag from your repository. If no releases or tags are found, it starts from version `0.0.0` and increments to `0.0.1`.

2. **Commit Messages:** It gathers all commit messages since the last release/tag and includes them in the release notes.

3. **Release Notes:** The commit messages are grouped under the "Changes in this release" section. If provided, the content of `add_description` is added as additional notes.

4. **Release Creation:** The action creates a new release on GitHub with the incremented version and the generated release notes.

## Local Development

To test or modify this action locally, you can build and run the Docker container manually:

```bash
docker build -t release-generator .
docker run -e GITHUB_TOKEN=your-token -e ADD_DESCRIPTION="This is a test release" release-generator
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

### Steps to Contribute:

1. Fork this repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.