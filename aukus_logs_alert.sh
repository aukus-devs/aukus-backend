#!/usr/bin/sh
sleep 5
tail -fn0 backend.log | \
while read line ; do
        echo "$line" | grep -i "error" | grep -v "errorlog"
        if [ $? = 0 ]
        then
             msg=${line//\"/\\\"} ; \
             #echo "test $msg"
             curl -i -H "Accept: application/json" -H "Content-Type:application/json" -X POST --data "{\"content\": \"$msg\"}" $DISCORD_WEBHOOK
        fi
done
