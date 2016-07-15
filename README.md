# TimeToCompleteGraph
Python and R scripts creating pdf with weekly time to complete graph for Jira project

**Usage**

python2.7 "timeToComplete.py" --password your_jira_password --user your_jira_user --jira https://your_jira_address --project jira_prefix_of_your_project


If executed correctly script will create 2 files:
* jiraIssues.csv - file with all jira issues that were loaded from Jira
* plot_toC.pdf - PDF file with chart


**Legend:**

* LT1W - issues completed in less then 1 week (green)
* GT1W - issues completed in between 1 and 2 weeks time (orange)
* GT2W - issues completed in more than 2 weeks (red)

![alt example chart](https://github.com/robert-krasinski/TimeToCompleteGraph/blob/master/plot_toC_pdf__1_page__and_Screen_Shot_2016-07-13_at_16_01_05.png?raw=true)

**Prerequisities**

* Python 2.7
* R (tested with R scripting front-end version 3.3.0) - https://www.r-project.org/
