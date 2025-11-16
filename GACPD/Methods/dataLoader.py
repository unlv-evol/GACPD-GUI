import os
import requests
import csv
import json
import sys
import re
import time
from datetime import datetime
from collections import defaultdict
import bitarray
import pickle
import difflib
from pprint import pprint

import Methods.common as common
import Methods.commitLoader as commitloader


def fetchPrData(source, destination, prs, destination_sha, token_list, ct):
    print('Fetching commit information and files from patches...')
    start = time.time()
    req = 0
    pr_data = {}
    lenTokens = len(token_list)
    
    for k in prs:
        try:
            pr_data[k] = {}

            # Get the PR
            if ct == lenTokens:
                ct = 0
            pr_request = 'https://api.github.com/repos/' + source + '/pulls/' + k
            pr = commitloader.apiRequest(pr_request, token_list[ct])
            ct += 1
            req += 1

            # Get the commit
            if ct == lenTokens:
                ct = 0
            commits_url = pr['commits_url']
            commits = commitloader.apiRequest(commits_url, token_list[ct])
            common.verbose_print(f'ct ={ct}')
            ct += 1
            req += 1

            commits_data = {}

            nr_files = pr['changed_files']

            pr_data[k]['pr_url'] = pr_request
            pr_data[k]['commits_url'] = commits_url
            pr_data[k]['changed_files'] = nr_files
            pr_data[k]['commits_data'] = list()
            pr_data[k]['destination_sha'] = destination_sha
            pr_data[k]['created_at'] = pr['created_at']
            pr_data[k]['merged_at'] = pr['merged_at']
            pr_data[k]['base_sha_added'] = pr['base']['sha']
            pr_data[k]['head_sha_added'] = pr['head']['sha']
            pr_data[k]['html_url'] = pr['html_url']
            pr_data[k]['title'] = pr['title']
            pr_data[k]['body'] = pr['body']
            
            for i in commits:
                if ct == lenTokens:
                    ct = 0
                commit_url = i['url']
                commit = commitloader.apiRequest(commit_url, token_list[ct])
                ct += 1
                req += 1

                try:
                    files = commit['files']
                    for j in files:
                        status = j['status']
                        file_name = j['filename']
                        print(file_name + "HERE")
                        added_lines = j['additions']
                        patched = j['patch']
                        removed_lines = j['deletions']
                        changes = j['changes']
                        file_ext = commitloader.get_file_type(file_name)
                        if file_name not in commits_data:
                            commits_data[file_name] = list()
                            if ct == lenTokens:
                                ct = 0
                            if commitloader.findFile(file_name, destination, token_list[ct], destination_sha):
                                sub = {}
                                sub['commit_url'] = commit_url
                                sub['commit_sha'] = commit['sha']
                                sub['commit_date'] = commit['commit']['committer']['date']
                                sub['parent_sha'] = commit['parents'][0]['sha']
                                sub['status'] = status
                                sub['additions'] = added_lines
                                sub['deletions'] = removed_lines
                                sub['patch'] = patched
                                sub['changes'] = changes
                                commits_data[file_name].append(sub)
                            ct += 1
                        else:
                            if ct == lenTokens:
                                ct = 0
                            if commitloader.findFile(file_name, destination, token_list[ct], destination_sha):
                                sub = {}
                                sub['commit_url'] = commit_url
                                sub['commit_sha'] = commit['sha']
                                sub['commit_date'] = commit['commit']['committer']['date']
                                sub['parent_sha'] = commit['parents'][0]['sha']
                                sub['status'] =status
                                sub['additions'] = added_lines
                                sub['deletions'] = removed_lines
                                sub['patch'] = patched
                                sub['changes'] = changes
                                commits_data[file_name].append(sub)
                            ct += 1
                except Exception as e:
                    print(e)
                    print('This should only happen if there are no files changed in a commit')
            pr_data[k]['commits_data'].append(commits_data)
        except Exception as e:
            print('An error occurred while fetching the pull request information from GitHub.')
            print (f'Error has to do with: {e}')

    end = time.time()
    runtime = end - start
    print('Fetch Runtime: ', runtime)
    
    return ct, pr_data, req, runtime

def getDestinationSha(destination, cut_off_date, token_list, ct):
    destination_sha = ''
    lenTokens = len(token_list)
    if ct == lenTokens:
        ct = 0
    cut_off_commits = commitloader.apiRequest('https://api.github.com/repos/' + destination +'/commits?until=' + cut_off_date, token_list[ct])
    ct += 1
    destination_sha = cut_off_commits[0]['sha']
    return destination_sha, ct


def find_file(filename, repo, token, sha):
    """
    find_file(filename, repo)
    Check if the file exists in the other repository

    Args:
        filename (String): the filename (including path) to be checked for existence
        repo (String): the repository in which the existence of the file must be checked
        token (String): the token for the api request
        sha (String): the GitHub sha
    """
    request_url = f"https://api.github.com/repos/{repo}/contents/{filename}?ref={sha}"
    response = commitloader.apiRequest(request_url, token)
    try:
        if response['path']:
            return True
        else:
            return False
    except Exception as e:
        return False

def fetch_pullrequest_data(mainline, variant, pullrequests, variant_sha, token_list, ct, cut_off_date,):
    print('Fetching files and commit information from patches...')
    start = time.time()
    req = 0
    pullrequest_data = {}
    # missing_files = []
    token_length = len(token_list)

    for pullrequest in pullrequests:
        try:
            pullrequest_data[pullrequest] = {}
            # used to include pr that contain java files only
            found = 0

            # Get the PR
            if ct == token_length:
                ct = 0

            pr_request = f'https://api.github.com/repos/{mainline}/pulls/{pullrequest}'
            pr = commitloader.apiRequest(pr_request, token_list[ct])
            ct += 1
            req += 1

            # merge_commit_sha = pr['merge_commit_sha']
            pullrequest_data[pullrequest]['pr_url'] = pr_request
            pullrequest_data[pullrequest]['created_at'] = pr['created_at']
            pullrequest_data[pullrequest]['merged_at'] = pr['merged_at']
            pullrequest_data[pullrequest]['merge_commit_sha'] = pr['merge_commit_sha']
            pullrequest_data[pullrequest]['commits'] = pr['commits']  # number of commits
            pullrequest_data[pullrequest]['changed_files'] = pr['changed_files']
            pullrequest_data[pullrequest]['commits_data'] = list()
            pullrequest_data[pullrequest]['destination_sha'] = variant_sha

            # get the commit sha before pull request creation date
            if ct == token_length:
                ct = 0

            pr_created_at = pr['created_at']
            until_date = datetime.strptime(pr_created_at, "%Y-%m-%dT%H:%M:%SZ")

            url = f'https://api.github.com/repos/{mainline}/commits?page=1&per_page=1&until={until_date}'
            last_commit_sha = commitloader.apiRequest(url, token_list[ct])
            pullrequest_data[pullrequest]['commit_sha_before'] = last_commit_sha[0]['sha']
            ct += 1
            req += 1

            # get files and patches
            if ct == token_length:
                ct = 0

            # files_merged = f'{constant.GITHUB_API_BASE_URL}{mainline}/commits/{merge_commit_sha}'
            files_merged = f'https://api.github.com/repos/{mainline}/pulls/{pullrequest}/files?page=1&per_page=100'
            pullrequest_files_merged = commitloader.apiRequest(files_merged, token_list[ct])
            ct += 1
            req += 1

            commits_data = {}
            try:
                for file in pullrequest_files_merged:

                    file_name = file['filename']
                    # # ignore non java files
                    # if file_name.endswith('.java'):
                    #     found = 1
                    commits_data[file_name] = list()
                    if ct == token_length:
                        ct = 0

                    if ('status' in file and 'additions' in file and 'deletions' in file and 'changes' in file
                            and 'patch' in file):
                        sub = {}
                        sub['status'] = file['status']
                        sub['additions'] = file['additions']
                        sub['deletions'] = file['deletions']
                        sub['changes'] = file['changes']
                        sub['patch'] = file['patch']
                        commits_data[file_name].append(sub)
                        # else:
                        # # print(f"File missing in target_head.......: {file_name}, Status: {file['status']}")

                        #     missing = {
                        #         'pullrequest_id': pullrequest,
                        #         'filename': file_name,
                        #         'status': file['status'],
                        #         'additions': file['additions'],
                        #         'deletions': file['deletions'],
                        #         'changes': file['changes']
                        #     }
                        #     missing_files.append(missing)
                    ct += 1
            except Exception as e:
                print(e)
                print('This should only happen if there are no files changed in a pull request')
            # if found == 0:
            #     pullrequest_data.pop(pullrequest)
            # else:
            pullrequest_data[pullrequest]['commits_data'].append(commits_data)
        except Exception as e:
            print(f"Error while trying to fetch pull request data....: {e} ..... {token_list[ct]}")

    # df = pd.DataFrame(missing_files)
    # df.to_csv('missing_files_java-apache.csv')

    end = time.time()
    runtime = end - start
    print("---%s seconds ---" % runtime)

    return ct, pullrequest_data, req, runtime