#! /bin/bash

END=1000
SL0=0.1
SL1=0.2
halcmd setp gasketing.mode 4

for ((i=1;i<=END;i++)); do
    echo $i
    halcmd setp gasketing.P-command 5
    sleep $SL0
	halcmd setp gasketing.P-command 6
    sleep $SL1
done
halcmd setp gasketing.mode 0
