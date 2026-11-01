#!/bin/sh
set -eu
case "$ROLE" in
  router) nft -f /rules.nft ;;
  server) ip route add 172.30.201.0/24 via 172.30.202.254 ;;
  allowed|denied) ip route add 172.30.202.0/24 via 172.30.201.254 ;;
esac
exec python /service.py
