# jiraLink
Links Todoist and Jira to make Jira a full scale todo app

Right now:
* jira connects directly to the url on port 80
  * apache receives this and runs a wsgi process
* todoist connects to ngrok
  * ngrok routes the request to port 5000 to a running python process
  
This had to be done because todoist requires a https port with a valid certificate
