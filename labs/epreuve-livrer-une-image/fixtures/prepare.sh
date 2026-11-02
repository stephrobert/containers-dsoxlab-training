#!/usr/bin/env bash
# Poser le banc de l'epreuve : TLS, deux comptes de droits inegaux, un registre.
#
# POURQUOI UN SERVEUR DE JETONS ET NON UN `htpasswd`. L'epreuve demande un compte
# EN LECTURE SEULE, et l'authentification par htpasswd de registry ne sait pas
# faire la difference : tout compte authentifie peut pousser. Seule une
# autorisation par jetons porte des droits par depot, et c'est elle qui permet de
# demander a l'apprenant de prouver qu'un client nu ne peut PAS publier.
#
# LE JWKS EST OBLIGATOIRE DEPUIS REGISTRY 3. Mesure du 2026-11-02 sur registry
# 3.1.2 : sans `auth.token.jwks`, le registre refuse tout jeton par « token
# signed by untrusted key with ID », et l'identifiant cite est pourtant celui de
# la cle du certificat declare en `rootcertbundle`. Registry 2 verifiait contre
# cette cle, la 3 ne regarde plus que le JWKS
# (distribution/distribution#4470).
#
# L'IDENTIFIANT DE CLE NE SE CHOISIT PAS : le registre compare le `kid` du jeton
# a ceux du JWKS, et le serveur de jetons calcule le sien a la facon de libtrust.
# Un JWKS valide au mauvais `kid` est refuse de la meme facon, sans que le
# message change d'un mot.
set -eu
cd /opt/lab-livraison
umask 077
mkdir -p certs auth build publisher client

HOTE="$1"

# --- TLS, une autorite jetable et un certificat de service -------------------
openssl req -x509 -newkey rsa:2048 -nodes -days 2 \
  -keyout certs/ca.key -out certs/ca.crt \
  -subj '/CN=dsoxlab livraison CA' \
  -addext 'basicConstraints=critical,CA:TRUE' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign'
openssl req -newkey rsa:2048 -nodes -keyout certs/server.key -out certs/server.csr \
  -subj '/CN=livraison.lab.test'
printf '%s\n' 'subjectAltName=DNS:livraison.lab.test' 'extendedKeyUsage=serverAuth' \
  'basicConstraints=critical,CA:FALSE' > certs/extensions.cnf
openssl x509 -req -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -out certs/server.crt -days 2 -extfile certs/extensions.cnf
chmod 644 certs/ca.crt certs/server.crt

python3 - <<'PY'
import base64
import hashlib
import json
import pathlib
import secrets
import subprocess

from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate


def b64u(n: int) -> str:
    brut = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(brut).rstrip(b"=").decode()


# Le JWKS que registry 3 exige, au `kid` que le serveur de jetons calculera.
publique = load_pem_x509_certificate(
    pathlib.Path("certs/server.crt").read_bytes()).public_key()
der = publique.public_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
b32 = base64.b32encode(hashlib.sha256(der).digest()[:30]).decode()
kid = ":".join(b32[i:i + 4] for i in range(0, len(b32), 4))
nombres = publique.public_numbers()
pathlib.Path("certs/jwks.json").write_text(json.dumps({
    "keys": [{"kty": "RSA", "alg": "RS256", "use": "sig", "kid": kid,
              "n": b64u(nombres.n), "e": b64u(nombres.e)}]
}, indent=2) + "\n")
pathlib.Path("certs/jwks.json").chmod(0o644)

# Deux comptes, deux mots de passe tires au hasard, deux niveaux de droits.
comptes = {nom: secrets.token_hex(24) for nom in ("publisher", "client")}
pathlib.Path("comptes.json").write_text(json.dumps(comptes))
pathlib.Path("comptes.json").chmod(0o600)
haches = {}
for nom, motdepasse in comptes.items():
    r = subprocess.run(["htpasswd", "-nBi", nom], input=motdepasse + "\n",
                       text=True, capture_output=True, check=True)
    haches[nom] = r.stdout.strip().split(":", 1)[1]

config = """server:
  addr: ":5401"
  certificate: /certs/server.crt
  key: /certs/server.key
token:
  issuer: dsoxlab-livraison
  expiration: 120
users:
"""
for nom, hache in haches.items():
    config += f'  "{nom}":\n    password: "{hache}"\n'
# LE PUBLISHER PUBLIE, LE CLIENT LIT. C'est la seule difference, et c'est ce
# que l'epreuve fait prouver dans les deux sens.
config += """acl:
  - match: {account: publisher, name: livraison/appli}
    actions: ["pull", "push"]
  - match: {account: client, name: livraison/appli}
    actions: ["pull"]
"""
pathlib.Path("auth.yml").write_text(config)
pathlib.Path("auth.yml").chmod(0o644)

# Le secret de construction, tire au hasard, et la preuve qu'on en attend.
# L'EMPREINTE ATTENDUE EST CELLE DU FICHIER, octet pour octet, et non celle de
# la chaine sans son retour a la ligne. Mesure du 2026-11-02 : la solution de
# reference employait `sha256sum < /run/secrets/jeton`, qui hache le FICHIER,
# donc le retour a la ligne compris, et le releve du banc attendait le hache de
# la chaine seule. Les deux ne coincidaient jamais, et le message accusait le
# candidat d'avoir ecrit une valeur inventee. L'enonce demande l'empreinte DU
# FICHIER, qui est ce que `sha256sum <fichier>` rend.
secret = secrets.token_hex(24)
contenu = (secret + "\n").encode()
pathlib.Path("build/jeton-de-build.txt").write_bytes(contenu)
pathlib.Path("build/jeton-de-build.txt").chmod(0o600)
attendu = hashlib.sha256(contenu).hexdigest()
pathlib.Path("/root/.lab-livraison.json").write_text(json.dumps({
    "secret": secret, "empreinte_attendue": attendu, "comptes": comptes,
}))
pathlib.Path("/root/.lab-livraison.json").chmod(0o600)
PY

cat > config.yml <<'YML'
version: 0.1
storage:
  filesystem:
    rootdirectory: /var/lib/registry
http:
  addr: :5000
  tls:
    certificate: /certs/server.crt
    key: /certs/server.key
auth:
  token:
    realm: https://livraison.lab.test:15402/auth
    service: dsoxlab-livraison
    issuer: dsoxlab-livraison
    rootcertbundle: /certs/server.crt
    # Obligatoire depuis registry 3 : voir l'entete de ce script.
    jwks: /certs/jwks.json
YML
chmod 644 config.yml

for image in \
  registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3 \
  cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464
do docker pull -q "$image" >/dev/null; done

docker run -d --name dsoxlab-livraison-auth \
  --label dsoxlab.lab=epreuve-livrer-une-image \
  -p "$HOTE:15402:5401" -v "$PWD:/config:ro" -v "$PWD/certs:/certs:ro" \
  cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464 \
  /config/auth.yml >/dev/null

docker run -d --name dsoxlab-livraison-registry \
  --label dsoxlab.lab=epreuve-livrer-une-image \
  -p "$HOTE:15401:5000" -v "$PWD/config.yml:/etc/distribution/config.yml:ro" \
  -v "$PWD/certs:/certs:ro" -v "$PWD/data:/var/lib/registry" \
  registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3 \
  >/dev/null
