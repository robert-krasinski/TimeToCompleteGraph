#!/usr/bin/env python

import csv
import datetime
import os
from collections import namedtuple
from restkit import Resource, BasicAuth
import json
import optparse
import sys
import time
import subprocess

reload(sys)
sys.setdefaultencoding('utf-8')


class Fetcher(object):
    """ This factory will create the actual method used to fetch issues from JIRA. This is really just a closure that saves us having
        to pass a bunch of parameters all over the place all the time. """

    def __init__(self, url, auth):
        self.url = url;
        self.auth = auth;

    def getJSON(self, url):
        resource = Resource(url, filters=[auth])
        response = resource.get(headers={'Content-Type': 'application/json'})
        if response.status_int == 200:
            # Not all resources will return 200 on success. There are other success status codes. Like 204. We've read
            # the documentation for though and know what to expect here.
            versions = json.loads(response.body_string())
            return versions
        else:
            print response.status_int
            # print response.
            return None


def parseArgs():
    parser = optparse.OptionParser()
    parser.add_option('-u', '--user', dest='user', default='user', help='Username to access JIRA')
    parser.add_option('-p', '--password', dest='password', default='pass', help='Password to access JIRA')
    parser.add_option('-j', '--jira', dest='jira_url', default='https://yourJira.atlassian.net', help='JIRA Base URL')
    parser.add_option('-x', '--project', dest='projectPrefix', default='your_project_prefix', help='Project prefix')

    return parser.parse_args()


# Class used for storing information about Jira issue
Issue = namedtuple('Issue',
                   ['project', 'key', 'updated', 'type', 'created',
                    'status',
                    'timeToComplete', 'movedToComplete'], verbose=False)


# Gets time in between dates in hours
def GetTimeInStatus(previousTransferDate, transferDate):
    if (previousTransferDate == None or transferDate == None): return None;
    prevTime = datetime.datetime.strptime(previousTransferDate[:-9], "%Y-%m-%dT%H:%M:%S")
    currTime = datetime.datetime.strptime(transferDate[:-9], "%Y-%m-%dT%H:%M:%S")

    return round((currTime - prevTime).total_seconds() / 60 / 60, 3);


finalStates = ['Completed', 'Rejected', 'Reviewed', 'Resolved', 'Closed']

if __name__ == '__main__':
    (options, args) = parseArgs()

print 'Options:\n'
print 'user: ' + options.user
print 'jira url: ' + options.jira_url
print 'project prefix: ' + options.projectPrefix



# measure time of script execution
start = time.time()

# Basic Auth is usually easier for scripts like this to deal with than Cookies.
auth = BasicAuth(options.user, options.password)

jsonFetcher = Fetcher(options.jira_url, auth)

startAt = 0
maxResults = 50

issueList = list();

# get issues in 50 item batches
while True:
    # get all issues except epics
    url = options.jira_url + "/rest/api/2/search?jql=project+in+%28" + options.projectPrefix + \
          "%29+and+type+not+in+%28Epic%29+ORDER+BY+created+ASC&expand=changelog&startAt=" + str(startAt)

    print url
    response = jsonFetcher.getJSON(url);

    # iterate through all issues downloaded
    for jsonIssue in response['issues']:

        key = jsonIssue['key']
        print key
        fields = jsonIssue['fields']

        previousTransferDate = None;

        timeToComplete = 0;
        lastTransitionToCompleteState = None;

        # iterate through events in issue history
        for history in jsonIssue['changelog']['histories']:

            transferDate = history['created']

            # iterate through fields that changed during history event
            for item in history['items']:
                # ignore updates that not include state change
                if item['field'] != 'status': continue;

                timeInFromStatus = GetTimeInStatus(previousTransferDate, transferDate)

                fromStatus = item['fromString']

                # don't calculate time spent on idle statuses http://stackoverflow.com/questions/4843158/check-if-a-python-list-item-contains-a-string-inside-another-string
                if any(fromStatus in s for s in finalStates):
                    # print 'skipping'
                    continue;

                toStatus = item['toString']

                if (toStatus in s for s in finalStates):
                    lastTransitionToCompleteState = transferDate

                timeToComplete += timeInFromStatus if (timeInFromStatus) else 0;

                previousTransferDate = transferDate  # previousTransferDate = issue.transferDate
                break;

        # for history in issue['histories']:
        issue = Issue(
            project=fields['project']['key'],
            key=key,
            # sprint=sprint.name if (sprint) else None,
            updated=fields['updated'],
            type=fields['issuetype']['name'],
            created=fields['created'],
            status=fields['status']['name'],
            timeToComplete=timeToComplete,
            movedToComplete=lastTransitionToCompleteState
        )
        issueList.append(issue)

    # check if all is retrieved
    startAt = startAt + maxResults;
    if (startAt >= response['total']):
        break;


issuesFilename = os.getcwd() + "/jiraIssues.csv"
issuesFilename = issuesFilename.replace(":", ".")

print issuesFilename

with open(issuesFilename, 'w') as f:
    w = csv.writer(f)
    w.writerow(
        ('project', 'key', 'updated', 'type', 'created',
         'status',
         'timeToComplete', 'movedToComplete'))  # field header
    for row in issueList:
        # print row
        w.writerow(row)

end = time.time()

#calculate execution time
print(end - start)

# Define command and arguments
command = 'Rscript'
path2script = 'TimeToCompleteGraph.R'

print 'Execute R script'

cmd = ['RScript', 'TimeToCompleteGraph.R', issuesFilename]
subprocess.check_output(cmd, universal_newlines=True)
