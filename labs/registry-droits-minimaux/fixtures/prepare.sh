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
  registry:2.8.3@sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373 \
  cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464 \
  alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f
do docker pull "$image"; done
docker run -d --name dsoxlab-registry-droits-minimaux-auth \
  --label dsoxlab.lab=registry-droits-minimaux \
  -p "$1:15448:5001" -v "$PWD:/config:ro" -v "$PWD/certs:/certs:ro" \
  cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464 \
  /config/auth.yml
docker run -d --name dsoxlab-registry-droits-minimaux-registry \
  --label dsoxlab.lab=registry-droits-minimaux \
  -p "$1:15447:5000" -v "$PWD/config.yml:/etc/docker/registry/config.yml:ro" \
  -v "$PWD/certs:/certs:ro" -v "$PWD/data:/var/lib/registry" \
  registry:2.8.3@sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373
