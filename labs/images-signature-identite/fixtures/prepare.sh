set -eu
cd /opt/lab-image-signature
umask 077
if docker image inspect dsoxlab-images-signature-identite:release >/dev/null 2>&1; then
  echo 'Refusing to replace an existing release image.' >&2
  exit 1
fi
mkdir keys trust product bench
docker image ls -aq > bench/baseline-images
base='alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f'
if docker image inspect "$base" >/dev/null 2>&1; then touch bench/base-existed; fi
openssl req -x509 -newkey rsa:2048 -nodes -days 2 \
  -keyout keys/ca.key -out trust/ca.crt -subj '/CN=dsoxlab image signing CA' \
  -addext 'basicConstraints=critical,CA:TRUE' -addext 'keyUsage=critical,keyCertSign,cRLSign'
for signer in approved other; do
  if test "$signer" = approved; then identity='spiffe://dsoxlab/release/builder'
  else identity='spiffe://dsoxlab/other/builder'; fi
  openssl req -newkey rsa:2048 -nodes -keyout "keys/$signer.key" \
    -out "keys/$signer.csr" -subj "/CN=$signer"
  printf '%s\n' "subjectAltName=URI:$identity" 'basicConstraints=critical,CA:FALSE' \
    'keyUsage=critical,digitalSignature' 'extendedKeyUsage=codeSigning' > keys/extensions.cnf
  openssl x509 -req -in "keys/$signer.csr" -CA trust/ca.crt -CAkey keys/ca.key \
    -CAcreateserial -out "keys/$signer.crt" -days 2 -extfile keys/extensions.cnf
done
openssl req -x509 -newkey rsa:2048 -nodes -days 2 -keyout keys/rogue.key -out keys/rogue.crt \
  -subj '/CN=untrusted' -addext 'subjectAltName=URI:spiffe://dsoxlab/release/builder' \
  -addext 'basicConstraints=critical,CA:FALSE' -addext 'keyUsage=critical,digitalSignature'
printf '%s\n' '{"identity":"spiffe://dsoxlab/release/builder","algorithm":"sha256"}' > trust/policy.json
cp trust/ca.crt bench/ca.crt
cp trust/policy.json bench/policy.json
openssl rand -hex 32 > product/release.txt
cp Dockerfile product/Dockerfile
docker pull "$base"
docker build -t dsoxlab-images-signature-identite:release product
docker save -o archive.tar dsoxlab-images-signature-identite:release
sha256sum archive.tar > bench/archive.sha256
openssl dgst -sha256 -sign keys/approved.key -out archive.sig archive.tar
chmod 644 trust/ca.crt keys/approved.crt keys/other.crt keys/rogue.crt
