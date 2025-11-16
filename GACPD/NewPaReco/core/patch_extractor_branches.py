import time
import os, sys, time, argparse
from datetime import datetime, timedelta
from NewPaReco.constants import constant
from NewPaReco.utils import helpers
import requests

class GetOutOfLoop(Exception):
    pass

API_URL = "https://api.github.com/graphql"
pr_set = set()

# Include issueCount so we can probe density
QUERY = """
query PRsIntoBranch($owner: String!, $name: String!, $branch: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(
      first: 100
      after: $after
      states: [MERGED]
      baseRefName: $branch
      orderBy: { field: CREATED_AT, direction: ASC }
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        url
        headRefName
        baseRefName
        createdAt
        mergedAt
      }
    }
  }
}
"""

def parse_iso_z(ts: str) -> datetime:
    # Expects e.g. "2018-08-28T17:08:43Z"
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

def run_query(token: str, query: str, variables: dict):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(API_URL, headers=headers, json={"query": query, "variables": variables})
    if r.status_code >= 500:
        time.sleep(1.2)
        r = requests.post(API_URL, headers=headers, json={"query": query, "variables": variables})
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]

def _rotate(ct, token_list):
    ct += 1
    if ct == len(token_list):
        ct = 0
    return ct

def _datestr(dt: datetime) -> str:
    return dt.date().isoformat()  # YYYY-MM-DD

def crawl_search_slice(repo, slice_start: datetime, slice_end: datetime,
                       token_list, ct, bug_keyword, start_dt, end_dt, print_rows=True):
    """
    Paginate a single date slice fully. Returns (added_prs, added_titles, ct, issueCount)
    """
    start_date_str = _datestr(slice_start)
    end_date_str = _datestr(slice_end)
    query_str = QUERY.format(repo=repo, start_date=start_date_str, end_date=end_date_str)

    pr = []
    title = []
    total_in_slice = 0

    after = None
    issue_count = None

    while True:
        data = run_query(token_list[ct], query_str, {"after": after})
        ct = _rotate(ct, token_list)

        block = data["search"]
        if issue_count is None:
            issue_count = block.get("issueCount", None)

        if print_rows is False:
            print("Not outputting obtained issues - just getting issue count")
            return pr, title, ct, (issue_count if issue_count is not None else 0)

        for node in block["nodes"]:
            pr_num = node["number"]
            pr_title = node["title"]
            pr_created = node["createdAt"]
            pr_merged = node["mergedAt"]
            pr_dt = parse_iso_z(pr_created)

            # Only print/keep if truly within the global bounds
            if pr_dt < start_dt or pr_dt > end_dt:
                continue

            if pr_merged is None:
                continue

            # bug keyword match
            low = pr_title.lower()
            if any(bug in low for bug in bug_keyword):
                if pr_num in pr_set:
                    continue

                title.append(pr_title)
                pr.append(pr_num)
                pr_set.add(pr_num)
                total_in_slice += 1

                if print_rows:
                    print(f"{pr_num},{pr_created},{pr_title}")

        if block["pageInfo"]["hasNextPage"]:
            after = block["pageInfo"]["endCursor"]
        else:
            break

    return pr, title, ct, (issue_count if issue_count is not None else 0)

def crawl_branch(repo_owner, repo_name, branch, token_list, ct, bug_keyword,
                 start_dt=None, end_dt=None, print_rows=True):
    """
    Full pagination over PRs merged into `branch` (ascending by createdAt).
    Optional start_dt/end_dt bound the results client-side.
    Returns (prs, titles, ct)
    """
    vars = {
        "owner": repo_owner,
        "name": repo_name,
        "branch": branch,
        "after": None
    }

    all_prs, all_titles = [], []
    while True:
        data = run_query(token_list[ct], QUERY, vars)
        ct = _rotate(ct, token_list)

        pulls = data["repository"]["pullRequests"]
        print(str(len(pulls["nodes"]))+" Total PRs")
        for pr in pulls["nodes"]:
            pr_num = pr["number"]
            pr_title = pr["title"]
            pr_created = pr["createdAt"]
            pr_merged = pr["mergedAt"]

            # merged-only already enforced by states:[MERGED], but keep the check if you like
            if pr_merged is None:
                continue

            if start_dt or end_dt:
                pr_dt = parse_iso_z(pr_created)
                if start_dt and pr_dt < start_dt:
                    # ascending: once we’re earlier than start_dt we can stop entirely
                    return all_prs, all_titles, ct
                if end_dt and pr_dt > end_dt:
                    # skip those past the upper bound; continue (don’t break)
                    continue

            low = pr_title.lower()
            if any(bug in low for bug in bug_keyword):
                if pr_num in pr_set:
                    continue
                pr_set.add(pr_num)
                all_prs.append(pr_num)
                all_titles.append(pr_title)
                if print_rows:
                    print(f"{pr_num},{pr_created},{pr_title}")

        if not pulls["pageInfo"]["hasNextPage"]:
            break
        vars["after"] = pulls["pageInfo"]["endCursor"]

    return all_prs, all_titles, ct


def pullrequest_patches_branch(repo, branch_name, token_list, ct):
    """
    Crawl all merged PRs into `branch_name` without search cap issues.
    `repo` is "owner/name".
    """
    start = time.time()

    owner, name = repo.split("/", 1)
    bug_keyword = helpers.unique(constant.BUGFIX_KEYWORDS)

    # If you still want global bounds, set them here (or pass as args)
    # start_dt = parse_iso_z("2018-08-28T17:08:43Z")
    # end_dt   = parse_iso_z("2018-12-31T18:26:45Z")
    start_dt = None
    end_dt = None

    print(owner, name, branch_name)

    prs, titles, ct = crawl_branch(
        repo_owner=owner,
        repo_name=name,
        branch=branch_name,
        token_list=token_list,
        ct=ct,
        bug_keyword=bug_keyword,
        start_dt=start_dt,
        end_dt=end_dt,
        print_rows=True
    )

    print(f"# Done. Printed {len(prs)} PRs.", file=sys.stderr)
    print(f"---{time.time() - start} seconds ---")
    pr_set.clear()
    return prs, titles, ct
