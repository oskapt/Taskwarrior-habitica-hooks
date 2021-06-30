#!/usr/bin/env bash

IMAGE=monachus/task2hab:latest
TASKRC=~/.taskrc
TASKDIR=~/.task
TASK=$(</dev/stdin)
KEY_KEY=habitica.api_key
USER_KEY=habitica.api_user

for arg in "$@"; do
  echo $arg | grep -qE "^rc:"
  if [[ $? -eq 0 ]]; then
    TASKRC=$(echo $arg | awk -F: '{ print $2 }')
    continue
  fi

  echo $arg | grep -qE "^data:"
  if [[ $? -eq 0 ]]; then
    TASKDIR=$(echo $arg | awk -F: '{ print $2 }')
    continue
  fi
done

API_USER=$(grep $USER_KEY $TASKRC | awk -F = '{ print $NF }')
API_KEY=$(grep $KEY_KEY $TASKRC | awk -F = '{ print $NF }')

if [[ -z $API_USER || -z $API_KEY ]]; then
  echo "Please set $USER_KEY and $KEY_KEY in $TASKRC"
  exit 1
fi

echo "$TASK" | docker run -i -e API_USER=$API_USER -e API_KEY=$API_KEY $IMAGE $@
