#!/usr/bin/sh
curl -x $AUKUS_SOCKS5_PROXY -i -H "Accept: application/json" -H "Content-Type:application/json" -X POST --data "{\"content\": \"v2025 ${AUKUS_HOST}: Booted\"}" $LOGS_DISCORD_WEBHOOK
tail -Fn0 backend.log | \
while read line ; do
        echo "$line" | grep -i "error" | grep -v "errorlog" | grep -v "See wait_timeout and interactive_timeout"
        if [ $? = 0 ]
        then
             msg=${line//\"/\\\"} ; \
             #echo "test $msg"
             curl -x $AUKUS_SOCKS5_PROXY -i -H "Accept: application/json" -H "Content-Type:application/json" -X POST --data "{\"content\": \"v2025 ${AUKUS_HOST}: $msg\"}" $LOGS_DISCORD_WEBHOOK
        fi
done
