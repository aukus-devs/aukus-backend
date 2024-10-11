#!/usr/bin/sh
tail -fn0 backend.log | \
while read line ; do
        echo "$line" | grep -i "error" | grep -v "errorlog"
        if [ $? = 0 ]
        then
             msg=${line//\"/\\\"} ; \
             #echo "test $msg"
             curl -x $SOCKS_5_PROXY -i -H "Accept: application/json" -H "Content-Type:application/json" -X POST --data "{\"content\": \"$msg\"}" $DISCORD_WEBHOOK
             curl -s -X POST -d "message_thread_id=18&chat_id=-1002471795184_18&text=${msg}" $TG_API
        fi
done
