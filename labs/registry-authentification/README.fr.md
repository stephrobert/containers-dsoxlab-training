# Protéger un registre TLS par authentification

La leçon exige un mot de passe et connecte le client. Ce cours regarde ce qui
échoue ou surprend : un hachage que le registre ne lit pas, un compte ajouté
sans redémarrage, ce que garde le client, une configuration incomplète, et un
fichier absent.

Vous travaillez dans `~/essai-acces`, sur le registre `essai-auth`, en HTTP sur
la boucle locale. Le challenge porte sur `registry-auth.lab.test` : n'y touchez
pas pendant le cours.

Page associée : [Servir un registre de confiance, et s'y authentifier](https://www.stephane-robert.info/docs/conteneurs/registres/distribution/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run registry-authentification
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La fonction `sert`
lance un registre qui lit un fichier de mots de passe, `code` rend le statut
HTTP d'un compte. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-acces && cd ~/essai-acces
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
export REG=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
mkdir auth
sert() { docker rm -f -v essai-auth > /dev/null 2>&1; docker run -d --name essai-auth -p 127.0.0.1:15951:5000 -v "$PWD/$1:/auth" -e REGISTRY_AUTH=htpasswd -e REGISTRY_AUTH_HTPASSWD_REALM=essai -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd "$REG" > /dev/null; sleep 2; }
code() { curl -s -o /dev/null -w '%{http_code}\n' ${1:+-u "$1"} http://127.0.0.1:15951/v2/; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔐 Exercice 1 : un hachage que le registre ne lit pas

Créez deux comptes, l'un en MD5, l'autre en bcrypt, et essayez-les :

```bash
htpasswd -nbm ana secret-ana | head -1 > auth/htpasswd
htpasswd -nbB bob secret-bob | head -1 >> auth/htpasswd
cut -c1-9 auth/htpasswd
sert auth
code ana:secret-ana
code bob:secret-bob
code
```

```text
ana:$apr1
bob:$2y$0
401
200
401
```

Le mot de passe d'`ana` est juste, et il est refusé : ce registre ne lit que
bcrypt, dont les lignes commencent par `$2y$`. Le refus est le même qu'un
mauvais mot de passe, 401. Regardez donc le début de la ligne avant d'accuser
l'utilisateur.

## ♻️ Exercice 2 : un compte ajouté sans redémarrage

Ajoutez un compte et retirez-en un, sans toucher au conteneur :

```bash
htpasswd -nbB zoe secret-zoe | head -1 >> auth/htpasswd
code zoe:secret-zoe
sed -i '/^bob/d' auth/htpasswd
code bob:secret-bob
```

```text
200
401
```

Le registre relit son fichier quand il change. Retirer une ligne ferme l'accès
aussitôt. Cela tient au montage d'un répertoire : un fichier monté seul et
remplacé ne serait pas revu.

## 🗝️ Exercice 3 : ce que garde le client

Connectez un client dans un dossier à lui, puis lisez ce qu'il a écrit :

```bash
echo secret-zoe | docker --config "$PWD/client" login -u zoe --password-stdin 127.0.0.1:15951 2> /dev/null
stat -c %a client/config.json
python3 -c "import json,base64; a=json.load(open('client/config.json'))['auths']; [print(k, base64.b64decode(v['auth']).decode()) for k, v in a.items()]"
docker tag "$IMAGE" 127.0.0.1:15951/essai:1
docker tag "$IMAGE" localhost:15951/essai:1
docker --config "$PWD/client" push -q 127.0.0.1:15951/essai:1 2> /dev/null | head -1
docker --config "$PWD/client" push -q localhost:15951/essai:1 2>&1 | grep -o 'no basic auth credentials'
docker --config "$PWD/client" logout 127.0.0.1:15951
docker rmi 127.0.0.1:15951/essai:1 localhost:15951/essai:1 > /dev/null
```

```text
Login Succeeded
600
127.0.0.1:15951 zoe:secret-zoe
127.0.0.1:15951/essai:1
no basic auth credentials
Removing login credentials for 127.0.0.1:15951
```

Le mot de passe est lisible par qui lit le fichier : base64 n'est pas un
chiffrement. Les identifiants sont rangés sous le nom exact du registre, port
compris : `localhost` et `127.0.0.1` sont deux registres différents pour le
client.

## 🧩 Exercice 4 : une configuration incomplète

Oubliez le `realm`, l'intitulé affiché à la demande du mot de passe :

```bash
docker run -d --name essai-panne -v "$PWD/auth:/auth" -e REGISTRY_AUTH=htpasswd -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd "$REG" > /dev/null; sleep 2
docker ps -a --filter name=essai-panne --format '{{.Status}}' | cut -d' ' -f1,2
docker logs essai-panne 2>&1 | grep -o '"realm" must be set.*'
docker rm -f -v essai-panne > /dev/null
```

```text
Exited (2)
"realm" must be set for htpasswd access controller
```

Le registre s'arrête au lieu de servir sans protection. Après un changement de
configuration, contrôlez que le conteneur tourne avant de tester un accès : un
registre arrêté refuse aussi tout le monde.

## 👻 Exercice 5 : un fichier absent

Donnez au registre un répertoire vide, et lisez son journal :

```bash
mkdir vide
sert vide
docker logs essai-auth 2>&1 | grep -o 'htpasswd is missing, provisioning with default user'
docker logs essai-auth 2>&1 | grep -oE 'user=[a-z]+'
code
code "docker:$(docker logs essai-auth 2>&1 | grep -oE 'password=[^ ]+' | cut -d= -f2)"
```

```text
htpasswd is missing, provisioning with default user
user=docker
401
200
```

Le fichier manquait, et le registre en a créé un avec un compte `docker`, dont
il écrit le mot de passe **dans son journal**. Quiconque lit les journaux a
donc un accès complet. Une faute dans le chemin monté suffit : cherchez cette
ligne à chaque mise en service.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f -v essai-auth > /dev/null
sudo rm -rf ~/essai-acces/vide
rm -rf ~/essai-acces
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset registry-authentification
dsoxlab check registry-authentification
```

```text
╭─ Résultat : registry-authentification ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests       │
╰────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un registre chiffré et ouvert à tous, à réserver à un
compte.

```bash
dsoxlab run registry-authentification
dsoxlab challenge registry-authentification
```
