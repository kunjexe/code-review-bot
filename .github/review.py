import os
import requests
from openai import OpenAI

# --- Get environment variables injected by GitHub Actions ---
openai_key = os.environ["OPENAI_API_KEY"]
github_token = os.environ["GITHUB_TOKEN"]
pr_number = os.environ["PR_NUMBER"]
repo = os.environ["REPO"]  # format: "username/repo-name"

# --- Step 1: Fetch the PR diff from GitHub API ---
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3.diff"  # this tells GitHub to return a diff
}

diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
response = requests.get(diff_url, headers=headers)
diff = response.text

# Limit diff size to avoid hitting token limits
# Most PRs are small but safety first
if len(diff) > 8000:
    diff = diff[:8000] + "\n\n[diff truncated due to length]"

# --- Step 2: Send the diff to OpenAI for review ---
client = OpenAI(api_key=openai_key)

prompt = f"""You are a senior software engineer doing a code review.
Review the following code diff and provide:
1. A brief summary of what changed
2. Any bugs or logic errors you spot
3. Security concerns if any
4. Suggestions for improvement
5. What was done well

Be constructive and concise. Use markdown formatting.

Code diff:
{diff}
"""

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)

review_comment = completion.choices[0].message.content

# --- Step 3: Post the review as a comment on the PR ---
comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
comment_headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json"
}

comment_body = f"## AI Code Review\n\n{review_comment}"
requests.post(comment_url, json={"body": comment_body}, headers=comment_headers)

print("Review posted successfully!")