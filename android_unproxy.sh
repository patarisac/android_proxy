#!/bin/bash

DIP="127.0.0.1"
DPORT="8082"
PKG=""
TARGETAPP_UID=""

while getopts "u:p:" opt; do
    case "$opt" in
        u) PKG="$OPTARG" ;;
        p) DPORT="$OPTARG" ;;
    esac
done

# fallback: positional port
if [ -z "$PKG" ] && [ -n "$1" ] && [[ "$1" =~ ^[0-9]+$ ]]; then
    DPORT="$1"
fi

# get UID
if [ -n "$PKG" ]; then
    TARGETAPP_UID=$(adb shell pm list packages -U | grep "$PKG" | sed 's/.*uid://')
    if [ -z "$TARGETAPP_UID" ]; then
        echo "Cannot find UID for $PKG"
        exit 1
    fi
    echo "Targeting UID: $TARGETAPP_UID"
fi

# build iptables rule
if [ -n "$TARGETAPP_UID" ]; then
    CMD_1="iptables -t nat -A OUTPUT -p tcp -m owner --uid-owner $TARGETAPP_UID -j DNAT --to-destination $DIP:$DPORT"
else
    CMD_1="iptables -t nat -A OUTPUT -p tcp ! --dport 27042 -j DNAT --to-destination $DIP:$DPORT"
fi

adb reverse tcp:$DPORT tcp:$DPORT

# privilege handling
if [ "$(adb shell whoami)" != "root" ]; then
    if [ "$(adb shell which su)" == "/system/bin/su" ]; then
        CMD_1="su -c '$CMD_1'"
    else
        CMD_1="su root sh -c '$CMD_1'"
    fi
fi

adb shell "$CMD_1"
echo "Proxy active → $DIP:$DPORT"

