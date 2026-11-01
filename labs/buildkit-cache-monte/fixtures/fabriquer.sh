#!/bin/sh
set -eu
source=$(cat /source/version.txt)
dependency=$(sha256sum /depot/dependency.txt | cut -d ' ' -f 1)
mkdir -p /cache /produit
if test -f "/cache/$dependency"; then
    origine=hit
else
    cp /depot/dependency.txt "/cache/$dependency"
    origine=miss
fi
empreinte=$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')
printf 'source=%s\ndependency=%s\ncache=%s\nempreinte=%s\n' \
    "$source" "$dependency" "$origine" "$empreinte" > /produit/receipt.txt
cat "/cache/$dependency" > /produit/dependency.txt
