#!/bin/bash

while true
do
	for i in `seq 1 600`;
	do
		./update_periodically.sh
		sleep 180
	done    
	./update_daily.sh
done
