#!/bin/sh
project_id=`jq '.project_id' project-d.json`
echo "${project_id}"