#!/bin/sh

if [ "$(id -u)" -ne 0 ]; then
  echo "You must run $0 as root."
  exit 1
fi

if [ ! -s /etc/rndc.key -a ! -s /etc/rndc.conf ]; then
  echo "Generating /etc/rndc.key"
  if /usr/sbin/rndc-confgen -a -A hmac-sha256 -r /dev/urandom > /dev/null 2>&1
  then
    chmod 640 /etc/rndc.key
    chown root:named /etc/rndc.key
    [ -x /sbin/restorecon ] && /sbin/restorecon /etc/rndc.key
    echo "/etc/rndc.key generated."
  else
    echo "/etc/rndc.key generation failed."
    exit 1
  fi
fi

/usr/sbin/named -u named -c /etc/named.conf -4

echo "The following output is now a tail of named.log:"
tail -f /var/named/log/named.log &
childPID=$!
wait $childPID
