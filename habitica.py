#!/usr/bin/env python3

from datetime import datetime
from os import getenv
import sys
import json
import requests
import re

URL = 'https://habitica.com/api/v3'

if len(sys.argv) == 1:
    print("The Habitica hook does not work with TaskWarrior API v1, please upgrade to Taskwarrior 2.4.3 or higher")
    sys.exit(1)

if not sys.argv[1] == "api:2":
    print("The Habitica hook only supports TaskWarrior API v2 at this time")
    sys.exit(1)

for arg in sys.argv:
    m = re.match(r'command:(.+)$', arg)
    if m:
        command = m.groups()[0]
        break

# Define constants to avoid magic values
COMMAND_ADD = 'add'
COMMAND_MODIFY = 'edit'
COMMAND_NEXT = 'next'
COMMAND_DELETE = 'delete'

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

HABITICA_DATA = 'data'
HABITICA_DATE = 'date'
HABITICA_DIFFICULTY = 'priority'
HABITICA_ERROR = 'err'
HABITICA_ID = 'id'

TASK_HABITICA_ID = 'id_habitica'
TASK_KEY_DESCRIPTION = 'description'
TASK_KEY_DIFFICULTY = 'priority'
TASK_KEY_DUE = 'due'
TASK_KEY_STATUS = 'status'
TASK_STATUS_COMPLETED = 'completed'
TASK_STATUS_DELETED = 'deleted'

API_USER = getenv('API_USER')
API_KEY = getenv('API_KEY')

try:
    DEBUG = bool(int(getenv('TASK_DEBUG', 0)))
except ValueError:
    DEBUG = False

headers = {
    'Content-Type': 'application/json',
    'x-api-user': API_USER,
    'x-api-key': API_KEY
}

priorityMap = {
    "L": "0.1",
    "None": "1",
    "M": "1.5",
    "H": "2"
}


class TaskException(Exception):
    ERROR_TIMEOUT = "Timeout while communicating with Habitica server"
    ERROR_CONNECTION = "Connection error while communicating with Habitica server"

    def __init__(self, timeout=False, connection=False, habitica_error=""):
        if not (timeout or connection or habitica_error):
            raise ValueError("At least one argument must be true")
        self.timeout = timeout
        self.connection = connection
        self.habitica_error = habitica_error

    def __str__(self):
        msg = ""
        if self.timeout:
            msg = self.ERROR_TIMEOUT
        elif self.connection:
            msg = self.ERROR_CONNECTION
        elif self.habitica_error:
            msg = self.habitica_error

        return "Error: {}".format(msg)

def log(data):
    '''
    Print data to stderr
    '''

    print(data, file=sys.stderr)

def pushTask(task):
    values = {
        "type": "todo",
        "text": task[TASK_KEY_DESCRIPTION],
        "notes": "Created from Taskwarrior"
    }

    # If task has due date, add to Habitica request
    if TASK_KEY_DUE in task:
        values[HABITICA_DATE] = datetime.strptime(task[TASK_KEY_DUE],
                                                  "%Y%m%dT%H%M%SZ").isoformat()

    # If task has difficulty, map to Habitica difficulty
    if TASK_KEY_DIFFICULTY in task and task[TASK_KEY_DIFFICULTY] in priorityMap:
        values[HABITICA_DIFFICULTY] = priorityMap[task[TASK_KEY_DIFFICULTY]]
    else:
        values[HABITICA_DIFFICULTY] = priorityMap['None']

    try:
        if TASK_HABITICA_ID not in task:
            # it's a new task
            req = requests.post(URL + '/tasks/user', data=json.dumps(values),
                            headers=headers, timeout=10)
        else:
            # it's an update
            req = requests.put(URL + '/tasks/' + task[TASK_HABITICA_ID],
                            data=json.dumps(values),
                            headers=headers, timeout=10)

        todo = req.json()
        if req.status_code >= 400:
            error = "Received HTTP error {} from Habitica API: {}".format(req.status_code, req.text)
            if HABITICA_ERROR in todo:
                error = todo[HABITICA_ERROR]
            raise TaskException(habitica_error=error)
        elif HABITICA_DATA not in todo:
            error = "Data object not found in Habitica response"
            raise TaskException(habitica_error=error)
        elif HABITICA_ID not in todo[HABITICA_DATA]:
            error = "Task ID not found in Habitica response"
            raise TaskException(habitica_error=error)
        else:
            return todo[HABITICA_DATA][HABITICA_ID]
    except requests.ConnectTimeout:
        raise TaskException(timeout=True)
    except requests.ConnectionError:
        raise TaskException(connection=True)


def add_task(task):
    id = pushTask(task)
    if id:
        task[TASK_HABITICA_ID] = id

def edit_task(task):
    id = pushTask(task)

def main():
    if DEBUG:
        log(sys.argv)

    task = original_task = json.loads(sys.stdin.readline())
    try:
        task = json.loads(sys.stdin.readline())
    except json.decoder.JSONDecodeError:
        # there was only one task
        pass
    response = []

    if command == COMMAND_ADD or (TASK_HABITICA_ID not in task and command != COMMAND_DELETE):
        add_task(task)
        if TASK_HABITICA_ID in task:
            response.append("Added task to Habitica")
        else:
            response.append("Failed to add task to Habitica, yet without error")

    if TASK_HABITICA_ID in task and command != COMMAND_ADD:
        if command == COMMAND_MODIFY:
            edit_task(task)
            response.append("Task edited on Habitica")
        elif task[TASK_KEY_STATUS] == TASK_STATUS_COMPLETED:
            complete_task(task)
            response.append("Task completed on Habitica")
        elif task[TASK_KEY_STATUS] == TASK_STATUS_DELETED:
            delete_task(task)
            response.append("Task deleted on Habitica")

    print(json.dumps(task))

    if response:
        print('\n'.join(response))

def complete_task(task):
    try:
        url = "{}/tasks/{}/score/up".format(URL, task[TASK_HABITICA_ID])
        requests.post(url, headers=headers, timeout=10)
    except requests.ConnectTimeout:
        raise TaskException(timeout=True)
    except requests.ConnectionError:
        raise TaskException(connection=True)

def delete_task(task):
    try:
        url = "{}/tasks/{}".format(URL, task[TASK_HABITICA_ID])
        requests.delete(url, headers=headers, timeout=10)
    except requests.ConnectTimeout:
        raise TaskException(timeout=True)
    except requests.ConnectionError:
        raise TaskException(connection=True)


if __name__ == '__main__':
    try:
        main()
        sys.exit(EXIT_SUCCESS)
    except TaskException as e:
        print(e)
        sys.exit(EXIT_FAILURE)
