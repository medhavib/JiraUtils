from jira import JIRA
import numpy as np
import pandas as pd
import xlsxwriter

import json

with open('jira.json') as json_data_file:
    data = json.load(json_data_file)
    username = data['auth']['username']
    password = data['auth']['password']
    queryadd = data['queryadd']
    domain = data['domain']
    columns = data['columns']

if not domain:
    domain = raw_input("Jira Domain (e.g https://XXX:PPP/jira): ")
        
if not username:
    username = raw_input("Username: ")

if not password:
    password = getpass.getpass("Password: ")

if not columns:
    columns = raw_input("Columns (List of colums): ")

if not queryadd:
    queryadd = raw_input("List of fixversions (no quotes, commas allowed):")
    queryadd = 'fixversion in (' + queryadd + ')'

def get_jira_client(domain, username, password):
    options = {'server': domain}
    return JIRA(options, basic_auth=(username, password))

def print_jira_issue(issue):
    print (issue['key'], ":", issue['fields']['summary'])

jira = get_jira_client(domain, username, password)

epics = jira.search_issues('type=epic and ' + queryadd, json_result=True, maxResults=1000)
stories = jira.search_issues('type=story and ' + queryadd, json_result=True, maxResults=1000)

epic_list = []
for epic in epics['issues']:
    epic['fields']['key'] = epic['key']
    epic_list.append(epic['fields'])

epics_df = pd.DataFrame(epic_list)

story_list = []
for story in stories['issues']:
    story['fields']['key'] = story['key']
    story_list.append(story['fields'])

stories_df = pd.DataFrame(story_list)

# Fetch all fields
allfields=jira.fields()
# Make a map from field name -> field id
nameMap = {field['name']:field['id'] for field in allfields}
idMap = {field['id']:field['name'] for field in allfields}

for column in epics_df.columns:
    if ('custom' in column):
        epics_df.rename(columns={column: idMap[column]}, inplace=True)


for column in stories_df.columns:
    if ('custom' in column):
        stories_df.rename(columns={column: idMap[column]}, inplace=True)

scope_df = pd.merge(epics_df, stories_df, how='right', on=None, left_on='key', right_on='Epic Link',
         left_index=False, right_index=False, sort=True,
         suffixes=('_epic', '_story'), copy=True, indicator=False,
         validate=None)

scope_df['status_story'] = scope_df['status_story'].dropna().apply(lambda x: x.get('name'))
scope_df['fixVersions_story'] = scope_df['fixVersions_story'].dropna().apply(lambda x: x[0].get('name'))
scope_df['Platform_story'] = scope_df['Platform_story'].dropna().apply(lambda x: x[0].get('value'))

#insert a column for jira link
scope_df['story_link'] = '=HYPERLINK("' + domain + '/browse/' + scope_df['key_story'] + '","' + scope_df['key_story'] + '")'

scope_df.to_excel('release.xlsx', index=False, sheet_name='Epics and Stories', freeze_panes=(1,0),
    columns=columns)
