#!/bin/bash
# Helper script to resubmit all jobs in error state
USERID=blim
while true
do
    for JOBID in $( alien_ps | grep -v '-' | grep -E $USERID'.*(E)' | awk '{print $2}' | sed 's/.*\(..........\)/\1/' );
        do   alien.py resubmit "$JOBID";
    done
    echo "done"
    sleep 600
done
