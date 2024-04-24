#!/bin/bash
# Fetch timezone and write to a global profile
echo "export TZ=$(curl -s https://ipinfo.io/timezone)" > /etc/profile.d/set_timezone.sh

# Now start up the container's main process
exec "$@"
