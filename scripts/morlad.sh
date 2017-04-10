#!/bin/bash

while true
do
	./update_daily.sh
	for i in `seq 1 600`;
	do
		./update_periodically.sh
		sleep 60
	done    
done
