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
QUERY_TEMPLATE = """
query($after: String) {{
  search(
    query: "repo:{repo} is:pr created:{start_date}..{end_date}",
    type: ISSUE,
    first: 100,
    after: $after
  ) {{
    issueCount
    nodes {{
      ... on PullRequest {{
        title
        number
        createdAt
        mergedAt
      }}
    }}
    pageInfo {{
      hasNextPage
      endCursor
    }}
  }}
}}
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
    query_str = QUERY_TEMPLATE.format(repo=repo, start_date=start_date_str, end_date=end_date_str)

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

def adaptive_windowed_crawl(repo, start_dt: datetime, end_dt: datetime,
                            token_list, ct, bug_keyword,
                            initial_days=90, dense_threshold=900, sparse_threshold=100,
                            min_days=1, max_days=365):
    """
    Walk from start_dt -> end_dt using adaptive windows to avoid 1k search cap.
    Returns (all_prs, all_titles, ct)
    """
    all_prs, all_titles = [], []

    current_start = start_dt
    window_days = initial_days

    while current_start <= end_dt:
        # Clamp window within global end
        current_end = min(current_start + timedelta(days=window_days - 1), end_dt)

        # First, probe issueCount for this slice (request once and throw results away),
        # then, if safe, re-run the slice and paginate fully.
        # We'll reuse crawl_search_slice for both probing and pagination to keep code simple.

        # Probe pass (no printing; we only need issueCount)
        _, _, ct_probe, issue_count = crawl_search_slice(
            repo, current_start, current_end, token_list, ct, bug_keyword,
            start_dt, end_dt, print_rows=False
        )
        ct = ct_probe  # advance token pointer

        # Adapt window size based on measured density
        if issue_count >= dense_threshold and window_days > min_days:
            # too dense -> shrink and retry same starting day
            window_days = max(min_days, window_days // 2)
            continue
        elif issue_count <= sparse_threshold and window_days < max_days:
            # very sparse -> expand for speed next iteration
            window_days = min(max_days, int(window_days * 1.5))

        # Now do the real pagination for this safe window (print rows)
        pr_slice, titles_slice, ct, _ = crawl_search_slice(
            repo, current_start, current_end, token_list, ct, bug_keyword,
            start_dt, end_dt, print_rows=True
        )
        all_prs.extend(pr_slice)
        all_titles.extend(titles_slice)

        # Move to next window (next day after current_end)
        current_start = current_end + timedelta(days=1)
    pr_set.clear()
    return all_prs, all_titles, ct

def pullrequest_patches(repo, diverge_date, least_date, token_list, ct):
    """
    Adaptive windowed crawl to defeat the 1k Search cap.
    """
    start = time.time()

    pr = []
    title = []

    bug_keyword = helpers.unique(constant.BUGFIX_KEYWORDS)

    # Validate timestamps (full ISO with Z)
    try:
        start_dt = parse_iso_z(diverge_date)
        end_dt = parse_iso_z(least_date)
    except ValueError:
        sys.exit('ERROR: Dates must be in: "YYYY-MM-DDTHH:MM:SSZ"')

    # Run adaptive windowed crawl
    pr, title, ct = adaptive_windowed_crawl(
        repo=repo,
        start_dt=start_dt,
        end_dt=end_dt,
        token_list=token_list,
        ct=ct,
        bug_keyword=bug_keyword,
        initial_days=120,
        dense_threshold=900,
        sparse_threshold=100,
        min_days=1,
        max_days=365
    )

    print(f"# Done. Printed {len(pr)} PRs.", file=sys.stderr)
    runtime = time.time() - start
    print(f"---{runtime} seconds ---")
    pr_set.clear()

    return pr, title, ct
