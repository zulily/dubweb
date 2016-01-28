#!/bin/bash
# This script will trigger dubweb to clone the budget for the current month
# into the next month. It was designed to be run on the 28th of the month. 
# Change the days on the NEXTMONTH generation if you run it at any other time.
CURMONTH=`/bin/date +%Y-%m`
NEXTMONTH=`/bin/date -d +5days +%Y-%m`
/usr/bin/curl -X POST --user (basicauth_username):(basicauth_password) --data "source=$CURMONTH&dest=$NEXTMONTH" https://(server)/data/budgets/clone
