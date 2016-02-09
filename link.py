from flask import Flask, request, json, Response
from jira import JIRA
import todoist
import perm
import uuid
import urllib3
urllib3.disable_warnings()

# setup Jira
jira = JIRA('https://circlelabs.atlassian.net', basic_auth=(perm.USERNAME, perm.PASSWORD))

# setup todoist 
api = todoist.TodoistAPI(perm.TODOISTAPI)

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/', methods=['POST'])
def todoist():
	json = request.get_json()
	todoId = json['event_data']['id']
	print(json)
	text = json['event_data']['content']	

	type = json['event_name']
	issue = jira.search_issues('project = TODO AND "Todoist ID" ~ "'+ str(todoId) +'"')
	if type == 'item:added':
		if len(issue) == 0:
			print('Adding Jira Issue')
			new_issue = jira.create_issue(project='TODO', summary=text, customfield_10025=str(todoId), issuetype={'name':'Task'})
		return ''
	
	issue = issue[0]
	if type == 'item:completed':
		print('Completing Jira Issue')
		jira.transition_issue(issue, '71')

	if type == 'item:uncompleted':
		print('Reverting Jira Issue')
		jira.transition_issue(issue, '101')

	if type == 'item:deleted':
		print('Deleting Jira Issue')
		issue.delete()

	return ''

@app.route('/test')
def test():
	issue = jira.issue('TODO-40')
	trans = jira.transitions(issue)

	return Response(json.dumps(trans), 200, {'Content-Type':'application/json'})
	# from open
	# to backlog = 11 someday
	# to To Do = 21 next
	# To Start = 31 today
	# Unecssary = 81 complete
	# 
	# From next
	# to Inprogress = 41 today
	# to Done = 61 complete
	# 
	# From today
	# to Done = 71
	# 
	# From done to open = 101

@app.route('/jira', methods=['POST'])
def main():
	json = request.get_json()

	title = json['issue']['fields']['summary']
	desc = json['issue']['fields']['description']
	todoId = json['issue']['fields']['customfield_10025']

	if desc == None:
		desc = ''

	print(todoId == None)

	event = json.get('webhookEvent', None)
	if event != None:
		if event.find('issue_created') != -1:
			text = title + "\n" + desc
			if (todoId == None):
				print('Creating Todoist Issue')
				unique = uuid.uuid4()
				temp = uuid.uuid4()
				item = api.sync(commands=[{'type':'item_add', 'temp_id':str(temp), 'uuid':str(unique), 'args':{'content':text}}])
				todoId = str(item['TempIdMapping'][str(temp)])
				jira.issue(json['issue']['key']).update(customfield_10025=todoId)
		elif event.find('issue_deleted') != -1:
			print('Deleting Todoist Issue')
			item = api.items.get_by_id(todoId)
			item.delete()

	trans = json.get('transition', None)
	if trans != None:
		if trans['to_status'] == 'Completed':
			print('Completing Todoist Item')
			item = api.items.get_by_id(todoId)
			item.complete()
		elif trans['to_status'] == 'Inbox':
			print('Reverting Todoist Item')
			item = api.items.get_by_id(todoId)
			item.uncomplete()

	api.commit()
	return ''


if __name__ == '__main__':
	app.run(debug=True)
