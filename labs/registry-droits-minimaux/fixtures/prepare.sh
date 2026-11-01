set -eu
cd /opt/lab-registry-rights
umask 077
mkdir certs data publisher reader product
openssl req -x509 -newkey rsa:2048 -nodes -days 2 -keyout certs/ca.key -out certs/ca.crt \
  -subj '/CN=dsoxlab rights CA' -addext 'basicConstraints=critical,CA:TRUE' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign'
openssl req -newkey rsa:2048 -nodes -keyout certs/server.key -out certs/server.csr \
  -subj '/CN=registry-rights.lab.test'
printf '%s\n' 'subjectAltName=DNS:registry-rights.lab.test' 'extendedKeyUsage=serverAuth' \
  'basicConstraints=critical,CA:FALSE' > certs/extensions.cnf
openssl x509 -req -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -out certs/server.crt -days 2 -extfile certs/extensions.cnf
chmod 644 certs/ca.crt certs/server.crt
python3 - <<'PY'
import json, secrets, subprocess, pathlib
users = {name: secrets.token_hex(24) for name in ("publisher", "reader")}
pathlib.Path("credentials.json").write_text(json.dumps(users))
hashes = {}
for name, password in users.items():
    result = subprocess.run(["htpasswd", "-nBi", name], input=password + "\n", text=True, capture_output=True, check=True)
    hashes[name] = result.stdout.strip().split(":", 1)[1]
config = """server:
  addr: ":5001"
  certificate: /certs/server.crt
  key: /certs/server.key
token:
  issuer: dsoxlab-rights
  expiration: 60
users:
"""
for name, hashed in hashes.items():
    config += f'  "{name}":\n    password: "{hashed}"\n'
config += """acl:
  - match: {account: publisher, name: catalogue/appli}
    actions: []
  - match: {account: reader, name: catalogue/appli}
    actions: []
"""
pathlib.Path("auth.yml").write_text(config)
pathlib.Path("product/release.txt").write_text(secrets.token_hex(24) + "\n")
PY
for image in \
  registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3 \
  cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464 \
  alpine@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
do docker pull "$image"; done
docker run -d --name dsoxlab-registry-droits-minimaux-auth \
  --label dsoxlab.lab=registry-droits-minimaux \
  -p "$1:15448:5001" -v "$PWD:/config:ro" -v "$PWD/certs:/certs:ro" \
  cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464 \
  /config/auth.yml
docker run -d --name dsoxlab-registry-droits-minimaux-registry \
  --label dsoxlab.lab=registry-droits-minimaux \
  -p "$1:15447:5000" -v "$PWD/config.yml:/etc/distribution/config.yml:ro" \
  -v "$PWD/certs:/certs:ro" -v "$PWD/data:/var/lib/registry" \
  registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
