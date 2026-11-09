import hashlib
import hmac
import json
import re
import urllib.request

from app.services.triage import run_triage

REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NEEDS_REVIEW_LABEL = "triage: needs review"
POSSIBLE_DUPLICATE_LABEL = "triage: possible duplicate"


def verify_signature(secret, body, header):
    """GitHub ke X-Hub-Signature-256 header ki jaanch. Secret na ho ya header ghalat ho to False."""
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


def severity_label(label):
    return f"severity: {label}"


def _inline(text, limit=120):
    """Text ko code ke andar rakhta hai, taake @naam se kisi ko ping na ho aur links na banen."""
    clean = " ".join(str(text).replace("`", "'").split())
    return "`" + (clean[: limit - 3] + "..." if len(clean) > limit else clean) + "`"


def build_comment(result):
    severity = result["severity"]
    lines = [
        "**Bug Report AI (automated suggestion)**",
        "",
        f"Suggested severity: **{severity['label']}** (confidence gap {severity['margin']:.2f})",
    ]
    if severity["needs_review"]:
        lines.append("")
        lines.append("The model is not sure about this one. Please check it.")
    if result["similar"]:
        lines.append("")
        lines.append("Similar earlier bugs:")
        for hit in result["similar"]:
            note = " (likely duplicate)" if hit["likely_duplicate"] else ""
            lines.append(f"- {hit['similarity']:.2f}{note}: {_inline(hit['text'])} (bug {hit['bug_id']}, {hit['project']})")
    lines.append("")
    lines.append(f"_A suggestion for a person to confirm, not a decision. Model: {result['model_version']}._")
    return "\n".join(lines)


def handle_issue_opened(payload, predictor, finder, post):
    """Naye GitHub issue par severity ka label aur ek comment lagata hai. post(url, data) bahar se aata hai."""
    issue = payload.get("issue") or {}
    repo = (payload.get("repository") or {}).get("full_name") or ""
    number = issue.get("number")
    title = " ".join(str(issue.get("title") or "").split())
    if not REPO_PATTERN.match(repo) or not isinstance(number, int) or len(title) < 3 or "pull_request" in issue:
        return None

    result = run_triage(predictor, finder, title, None, top_k=3, min_similarity=0.6)
    labels = [severity_label(result["severity"]["label"])]
    if result["severity"]["needs_review"]:
        labels.append(NEEDS_REVIEW_LABEL)
    if any(hit["likely_duplicate"] for hit in result["similar"]):
        labels.append(POSSIBLE_DUPLICATE_LABEL)

    base = f"https://api.github.com/repos/{repo}/issues/{number}"
    post(base + "/labels", {"labels": labels})
    post(base + "/comments", {"body": build_comment(result)})
    return {"labels": labels}


def make_poster(token):
    def post(url, data):
        request = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "bug-report-ai",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status

    return post
