# Garder un jeton runtime hors de l'environnement

La leçon remplace une variable par un fichier monté. Ce cours suit le secret
après sa livraison : ce qui hérite d'une variable, ce qui sort d'un fichier
monté, une rotation qui ne se voit pas, une empreinte fausse, une commande
diffusée, et un secret de Compose écrit dans le conteneur.

Vous travaillez dans `~/essai-jeton`, avec une valeur inventée, `essai-valeur`.
Le challenge porte sur le `worker` de son projet et son jeton : n'y touchez pas
pendant le cours.

Page associée : [Garder un secret hors de l'environnement](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/secrets/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run secrets-au-runtime
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-jeton && cd ~/essai-jeton
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
printf 'essai-valeur' > jeton && chmod 600 jeton
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🌿 Exercice 1 : ce qui hérite d'une variable

Passez la valeur par `-e`, puis retrouvez-la dans trois endroits :

```bash
docker run -d --init --name essai-env -e JETON=essai-valeur "$IMAGE" sleep 600 > /dev/null
docker exec essai-env sh -c 'sh -c "env | grep JETON"'
sudo cat "/proc/$(docker inspect essai-env --format '{{.State.Pid}}')/environ" | tr '\0' '\n' | grep JETON
docker commit essai-env essai-image > /dev/null
docker inspect essai-image --format '{{json .Config.Env}}' | grep -o 'JETON=[a-z-]*'
docker rm -f essai-env > /dev/null; docker rmi -f essai-image > /dev/null
```

```text
JETON=essai-valeur
JETON=essai-valeur
JETON=essai-valeur
```

Chaque processus enfant reçoit la variable, l'hôte la lit, et `docker commit`
l'écrit dans l'image. Une image publiée ensuite emporte le secret.

## 📤 Exercice 2 : ce qui sort d'un fichier monté

Montez le fichier, puis essayez de le récupérer par quatre moyens :

```bash
docker run -d --init --name essai-fichier -v "$PWD/jeton:/run/secrets/jeton:ro" "$IMAGE" sleep 600 > /dev/null
docker exec --user 1000 essai-fichier cat /run/secrets/jeton
docker cp -q essai-fichier:/run/secrets/jeton copie && cat copie; echo
docker export essai-fichier | tar xO run/secrets/jeton | wc -c
docker commit essai-fichier essai-image > /dev/null
docker run --rm essai-image sh -c 'wc -c < /run/secrets/jeton'
docker rmi -f essai-image > /dev/null
```

```text
cat: can't open '/run/secrets/jeton': Permission denied
essai-valeur
0
0
```

Le fichier garde les droits de l'hôte : un compte ordinaire ne le lit pas.
L'export et l'image n'en contiennent qu'un fichier vide, le point de montage.
`docker cp`, lui, suit le montage : qui pilote le moteur lit le secret.

## 🔄 Exercice 3 : une rotation qui ne se voit pas

Remplacez le fichier par un nouveau, puis modifiez-le sur place :

```bash
lit() { docker exec essai-fichier cat /run/secrets/jeton; echo; }
printf 'valeur-2' > neuf && chmod 600 neuf && mv neuf jeton
lit
docker restart --timeout 1 essai-fichier > /dev/null && lit
printf 'valeur-3' > jeton && lit
docker rm -f essai-fichier > /dev/null
```

```text
essai-valeur
valeur-2
valeur-3
```

Après `mv`, le conteneur lit encore l'ancienne valeur : le montage tient au
fichier, pas à son nom. Un redémarrage la met à jour. Écrire sur place se voit
aussitôt, mais l'application peut lire au milieu de l'écriture.

## #️⃣ Exercice 4 : une empreinte fausse

Comparez l'empreinte de la même valeur, écrite de deux façons :

```bash
echo 'essai-valeur' | sha256sum | cut -c1-12
printf 'essai-valeur' | sha256sum | cut -c1-12
echo 'essai-valeur' | wc -c; printf 'essai-valeur' | wc -c
```

```text
622e72c5798f
e3e48e631510
13
12
```

`echo` ajoute un retour à la ligne, qui change l'empreinte et fait échouer bien
des connexions. Écrivez un secret avec `printf`, et comparez des tailles avant
de chercher plus loin.

## 📻 Exercice 5 : une commande diffusée

Passez la valeur à `docker exec` de deux façons, et lisez les événements du
moteur :

```bash
docker run -d --init --name essai-cmd "$IMAGE" sleep 600 > /dev/null
DEBUT=$(date +%s)
docker exec -e JETON=essai-valeur essai-cmd true
docker exec essai-cmd true --jeton essai-valeur
sleep 1
docker events --since "$DEBUT" --until "$(date +%s)" --filter container=essai-cmd --format '{{.Action}}' | grep exec_create
docker rm -f essai-cmd > /dev/null
```

```text
exec_create: true
exec_create: true --jeton essai-valeur
```

Les arguments d'une commande partent dans les événements, que tout outil
branché sur le moteur peut lire. La variable n'y est pas, mais elle reste
lisible sur l'hôte. Donnez un secret par l'entrée de la commande, ou par un
fichier.

## 🧾 Exercice 6 : un secret de Compose écrit dans le conteneur

Déclarez un secret dont la source est une variable, et cherchez où il se trouve
:

```bash
cat > compose.yaml <<EOF
services:
  a:
    image: $IMAGE
    command: sleep 600
    init: true
    network_mode: none
    secrets: [jeton]
secrets:
  jeton:
    environment: JETON
EOF
JETON=essai-valeur docker compose -p essai-secret up -d > /dev/null 2>&1
docker inspect essai-secret-a-1 | grep -c essai-valeur
docker inspect essai-secret-a-1 --format '{{json .Mounts}}'
docker diff essai-secret-a-1 | grep secrets
docker exec essai-secret-a-1 stat -c '%a %U' /run/secrets/jeton
docker export essai-secret-a-1 | tar xO run/secrets/jeton; echo
JETON=x docker compose -p essai-secret down --timeout 1 > /dev/null 2>&1
```

```text
0
[]
A /run/secrets
A /run/secrets/jeton
444 root
essai-valeur
```

L'inspection ne le montre pas, et aucun montage n'existe : Compose a copié la
valeur dans la couche du conteneur, lisible par tous ses comptes. L'export
l'emporte. Une source `file` donne un montage ; c'est elle qu'il faut pour un
vrai secret.

## 🧹 Nettoyage

```bash
cd ~
rm -rf ~/essai-jeton
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
dsoxlab reset secrets-au-runtime
dsoxlab check secrets-au-runtime
```

```text
╭── Résultat : secrets-au-runtime ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un jeton à livrer, que rien ne doit laisser fuir.

```bash
dsoxlab run secrets-au-runtime
dsoxlab challenge secrets-au-runtime
```
