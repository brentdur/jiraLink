from flask import Flask, request
from jira import JIRA
import todoist

# setup Jira
jira = JIRA('https://circlelabs.atlassian.net', basic_auth=('admin', ''))

# setup todoist 
api = todoist.TodoistAPI('')

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/', methods=['POST'])
def todoist():
	json = request.get_json()
	todoId = json['event_data']['id']
	text = json['event_data']['content']

	type = json['event_name']

	if type == 'item:added':
		new_issue = jira.create_issue(project='TODO', summary=text, customfield_10025=str(todoId), issuetype={'name':'Task'})
		return ''
	
	issue = jira.search_issues('project = TODO AND "Todoist ID" ~ "'+ str(todoId) +'"')[0]
	if type == 'item:completed':
		jira.transition_issue(issue, '21')

	if type == 'item:uncompleted':
		jira.transition_issue(issue, '51')

	if type == 'item:deleted':
		issue.delete()

	return ''

@app.route('/jira', methods=['POST'])
def main():
	json = request.get_json()

	title = json['issue']['fields']['summary']
	desc = json['issue']['fields']['description']
	todoId = json['issue']['fields']['customfield_10025']

	if desc == None:
		desc = ''

	event = json.get('webhookEvent', None)
	if event != None:
		if event.find('issue_created') != -1:
			text = title + "\n" + desc
			item = api.items.add(text, None)
			todoId = item['id']
			jira.issue(json['issue']['key']).update(customfield_10025=todoId)
		elif event.find('issue_deleted') != -1:
			item = api.items.get_by_id(todoId)
			item.delete()

	trans = json.get('transition', None)
	if trans != None:
		if trans['to_status'] == 'Done':
			item = api.items.get_by_id(todoId)
			item.complete()
		elif trans['to_status'] == 'To Do':
			item = api.items.get_by_id(todoId)
			item.uncomplete()

	api.commit()
	return ''


if __name__ == '__main__':
	app.run(debug=True)