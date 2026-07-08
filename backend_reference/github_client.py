"""
Minimal GitHub Contents API client used to read/write files in the
TechnicalAnalysis-routines repo from outside a git clone (safe to call from a
stateless Celery worker - no local checkout or git credentials needed).
"""

import base64

import requests

GITHUB_API_ROOT = "https://api.github.com"


def get_file(repo, path, branch, token):
    """
    Return (decoded_content_str, sha) for the file at path on branch.
    Returns (None, None) if the file does not exist yet.
    """
    resp = requests.get(
        f"{GITHUB_API_ROOT}/repos/{repo}/contents/{path}",
        params={"ref": branch},
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    if resp.status_code == 404:
        return None, None
    resp.raise_for_status()
    body = resp.json()
    content = base64.b64decode(body["content"]).decode("utf-8")
    return content, body["sha"]


def put_file(repo, path, branch, token, content_str, message, sha=None):
    """
    Create or update the file at path on branch with content_str.
    Pass the sha returned by get_file() when updating an existing file;
    omit it when creating a new file.
    """
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(
        f"{GITHUB_API_ROOT}/repos/{repo}/contents/{path}",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
