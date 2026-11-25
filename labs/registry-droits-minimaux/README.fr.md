# Accorder les droits minimaux à un éditeur et un lecteur distinct

Un mot de passe dit qui vous êtes. Il ne dit pas ce que vous pouvez faire. Avec
un fichier `htpasswd`, tous les comptes ont les mêmes droits. Pour les séparer,
le registre délègue la décision à un service de jetons : le client s'y
connecte, demande une action sur un dépôt, et reçoit un jeton signé qui porte
ce qui lui est accordé. Le registre vérifie la signature et applique. Ce cours
monte les deux services et lit ce qui circule entre eux.

Vous travaillez sur `essai-registre` et `essai-auth`, en HTTP sur la boucle
locale : cela suffit pour lire les échanges, pas pour un service joint par
d'autres machines. Le challenge porte sur `/opt/lab-registry-rights` et sur les
conteneurs `dsoxlab-registry-droits-minimaux-*` : n'y changez rien pendant le
cours. Le cours copie seulement leur clé de signature, pour ne pas en fabriquer
une autre.

Page associée : [Servir un registre de confiance, et s'y authentifier](https://www.stephane-robert.info/docs/conteneurs/registres/distribution/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run registry-droits-minimaux
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `regles` écrit la
configuration du service de jetons avec les règles que vous lui donnez, et le
relance. `jeton` demande un jeton ; `lire` affiche le compte, la durée en
secondes et ce qui est accordé. **Gardez le même terminal jusqu'au nettoyage**
: les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-droits && cd ~/essai-droits
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
R=127.0.0.1:15547; T=http://127.0.0.1:15548/auth
mkdir conf cles
sudo cp /opt/lab-registry-rights/certs/server.crt /opt/lab-registry-rights/certs/server.key /opt/lab-registry-rights/certs/jwks.json cles/
sudo chown -R $(id -u) cles
for u in lea noe; do (umask 077; openssl rand -hex 12 > $u); done
pret() { for i in $(seq 20); do curl -s -o /dev/null $T && return; sleep 0.5; done; }
regles() { { printf 'server: {addr: ":5001"}\ntoken: {issuer: essai, expiration: 60, certificate: /cles/server.crt, key: /cles/server.key}\nusers:\n'; for u in lea noe; do printf '  %s: {password: "%s"}\n' $u "$(htpasswd -niB $u < $u | head -1 | cut -d: -f2)"; done; printf 'acl:\n'; cat; } > conf/auth.yml; docker restart -t 1 essai-auth > /dev/null 2>&1; pret; }
jeton() { printf 'user = "%s:%s"\n' $1 $(cat $1) | curl -sK - "$T?service=essai&scope=repository:$2:$3" | python3 -c 'import json, sys; print(json.load(sys.stdin)["token"])'; }
cat > lire.py <<'EOF'
import base64, json, sys
d = json.loads(base64.urlsafe_b64decode(sys.stdin.read().split(".")[1] + "=="))
print(d["sub"], d["exp"] - d["iat"], "s :", d["access"][0]["name"], d["access"][0]["actions"])
EOF
lire() { python3 lire.py; }
image() { printf 'FROM %s\nRUN echo %s > /v\n' "$IMAGE" $2 | docker build -q -t $R/atelier/outil:$1 - > /dev/null; }
docker run -d --name essai-auth -p 127.0.0.1:15548:5001 -v $PWD/conf:/conf:ro -v $PWD/cles:/cles:ro cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464 /conf/auth.yml > /dev/null
docker run -d --name essai-registre -p $R:5000 -v $PWD/cles:/cles:ro -e REGISTRY_AUTH=token -e REGISTRY_AUTH_TOKEN_REALM=$T -e REGISTRY_AUTH_TOKEN_SERVICE=essai -e REGISTRY_AUTH_TOKEN_ISSUER=essai -e REGISTRY_AUTH_TOKEN_ROOTCERTBUNDLE=/cles/server.crt -e REGISTRY_AUTH_TOKEN_JWKS=/cles/jwks.json registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3 > /dev/null
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🚪 Exercice 1 : connecté, et sans aucun droit

Donnez une règle vide, lisez ce que le registre répond sans identifiant,
connectez-vous, puis poussez :

```bash
regles <<'EOF'
  - match: {account: lea, name: atelier/outil}
    actions: []
EOF
curl -si http://$R/v2/ | grep -iE '^HTTP|www-auth'
for u in lea noe; do docker --config $PWD/cfg-$u login $R -u $u --password-stdin < $u 2>&1 | grep -o 'Login Succeeded'; done
echo faux | docker --config $PWD/cfg-faux login $R -u lea --password-stdin 2>&1 | grep -o 'Auth failed'
image 1 un
docker --config $PWD/cfg-lea push -q $R/atelier/outil:1 2>&1 | grep -o 'insufficient_scope'
jeton lea atelier/outil pull,push | lire
```

```text
HTTP/1.1 401 Unauthorized
Www-Authenticate: Bearer realm="http://127.0.0.1:15548/auth",service="essai"
Login Succeeded
Login Succeeded
Auth failed
insufficient_scope
lea 60 s : atelier/outil []
```

Le `401` nomme le service à qui s'adresser. La connexion réussit, car le mot de
passe est juste, et le push est refusé : `insufficient_scope` veut dire que le
compte est connu, mais pas autorisé. Le jeton le montre : une liste vide.
`--config` range les identifiants dans un dossier à part, sans toucher aux
vôtres.

## 🎫 Exercice 2 : demandé, et accordé

Donnez à `lea` de quoi publier et à `noe` de quoi lire, puis demandez trop :

```bash
regles <<'EOF'
  - match: {account: lea, name: atelier/outil}
    actions: [pull, push]
  - match: {account: noe, name: atelier/outil}
    actions: [pull]
EOF
jeton lea atelier/outil pull,push | lire
jeton noe atelier/outil pull,push,delete | lire
jeton lea autre/outil pull,push | lire
docker --config $PWD/cfg-lea push -q $R/atelier/outil:1
```

```text
lea 60 s : atelier/outil ['pull', 'push']
noe 60 s : atelier/outil ['pull']
lea 60 s : autre/outil []
127.0.0.1:15547/atelier/outil:1
```

Le service accorde la partie de la demande que les règles permettent, sans
erreur. Demander n'est donc pas obtenir : lisez le jeton, pas la demande. Une
demande qu'aucune règle ne couvre donne une liste vide. Publier demande `pull`
et `push`, car le client regarde d'abord ce qui existe déjà.

## 👻 Exercice 3 : un push qui réussit sans rien écrire

Faites pousser le lecteur trois fois : la même image, un contenu neuf, un
nouveau nom :

```bash
ecrits() { docker logs essai-registre 2>&1 | grep -c '"PUT /v2/'; }
N=$(ecrits)
docker --config $PWD/cfg-noe push -q $R/atelier/outil:1; echo "identique : rc=$?, demandes d'ecriture : $(( $(ecrits) - N ))"
image 2 deux
docker --config $PWD/cfg-noe push -q $R/atelier/outil:2 2>&1 | grep -o 'insufficient_scope'
docker tag $R/atelier/outil:1 $R/atelier/outil:bis
docker --config $PWD/cfg-noe push -q $R/atelier/outil:bis 2>&1 | grep -o 'insufficient_scope'
[ "$(ecrits)" -gt "$N" ] && echo 'cette fois, une demande est partie'
```

```text
127.0.0.1:15547/atelier/outil:1
identique : rc=0, demandes d'ecriture : 0
insufficient_scope
insufficient_scope
cette fois, une demande est partie
```

Le premier push rend 0 et pourtant `noe` n'a aucun droit d'écriture : tout
était déjà là, le client n'a rien envoyé. Le journal du registre le confirme,
aucune demande d'écriture n'est arrivée. Pour éprouver un refus, poussez
toujours un contenu inédit.

## 🔀 Exercice 4 : l'ordre et la portée des règles

Placez une règle large avant une règle précise, puis regardez ce que couvre un
joker :

```bash
regles <<'EOF'
  - match: {account: noe}
    actions: [pull]
  - match: {account: noe, name: atelier/outil}
    actions: [pull, push]
  - match: {account: lea, name: "atelier/*"}
    actions: [pull, push]
EOF
jeton noe atelier/outil pull,push | lire
jeton noe secret/plans pull | lire
for n in atelier/outil atelier/outil/v2 atelier; do jeton lea $n push | lire; done
```

```text
noe 60 s : atelier/outil ['pull']
noe 60 s : secret/plans ['pull']
lea 60 s : atelier/outil ['push']
lea 60 s : atelier/outil/v2 []
lea 60 s : atelier []
```

La première règle qui correspond décide : la seconde n'est jamais lue pour
`noe`, et l'oubli du dépôt lui ouvre `secret/plans` en lecture. Le joker
s'arrête au `/` : `atelier/*` ne couvre ni `atelier` ni `atelier/outil/v2`.
Nommez le compte et le dépôt dans chaque règle.

## 🧯 Exercice 5 : une faute de frappe, et plus rien ne sort

Cassez le fichier de règles, relancez, et tirez une image déjà publiée :

```bash
cp conf/auth.yml bon.yml
printf '  - match: {account: noe\n' >> conf/auth.yml
docker restart -t 1 essai-auth > /dev/null; sleep 2
docker ps -a --filter name=essai-auth --format '{{.State}}'
docker logs --tail 1 essai-auth 2>&1 | grep -o 'Failed to load config.*yaml: line [0-9]*'
docker --config $PWD/cfg-lea pull -q $R/atelier/outil:1 2>&1 | grep -o 'connection refused'
docker ps --filter name=essai-registre --format '{{.State}}'
cp bon.yml conf/auth.yml; docker start essai-auth > /dev/null; pret
docker --config $PWD/cfg-lea pull -q $R/atelier/outil:1
```

```text
exited
Failed to load config: could not parse config: yaml: line 13
connection refused
running
127.0.0.1:15547/atelier/outil:1
```

Le registre tourne et personne ne peut plus lire : sans service de jetons,
aucune demande n'aboutit. Le message du client parle d'une connexion refusée,
pas de droits. Le journal du service donne la ligne fautive. Gardez une copie
du fichier avant de le changer.

## ⏳ Exercice 6 : un droit retiré, un jeton encore bon

Prenez un jeton de lecture, retirez le droit, puis servez-vous du jeton
aussitôt et plus tard :

```bash
J=$(jeton noe atelier/outil pull)
regles <<'EOF'
  - match: {account: noe, name: atelier/outil}
    actions: []
EOF
jeton noe atelier/outil pull | lire
avec() { printf 'header = "Authorization: Bearer %s"\n' "$J" | curl -sK - -o /dev/null -w '%{http_code}\n' -H 'Accept: application/vnd.oci.image.index.v1+json' http://$R/v2/atelier/outil/manifests/1; }
avec
sleep 75; avec
sleep 60; avec
```

```text
noe 60 s : atelier/outil []
200
200
401
```

Le registre ne redemande rien au service : il croit le jeton jusqu'à son
échéance. Le retrait n'a donc pas d'effet immédiat. Le jeton annonçait 60
secondes et il passait encore après 75 : le registre tolère un décalage
d'horloge, une minute de plus d'après notre mesure. C'est pourquoi ces jetons
sont courts.

## 🧹 Nettoyage

```bash
cd ~
docker rm -fv essai-auth essai-registre > /dev/null
docker images --format '{{.Repository}}:{{.Tag}}' | grep '15547' | xargs -r docker rmi -f > /dev/null
rm -rf ~/essai-droits
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c 'essai-\|15547'
```

```text
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset registry-droits-minimaux
dsoxlab check registry-droits-minimaux
```

```text
╭─ Résultat : registry-droits-minimaux ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests      │
╰───────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un éditeur, un lecteur sur une autre machine, et des
droits à poser sans en donner trop.

```bash
dsoxlab run registry-droits-minimaux
dsoxlab challenge registry-droits-minimaux
```
