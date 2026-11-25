# Écrire les tests qui refusent une image cassée

La leçon écrit un script de tests complet. Ce cours montre cinq raisons pour
lesquelles un test écrit de bonne foi accepte ce qu'il devrait refuser : un
échec avalé par le shell, une réponse 500 prise pour un succès, un message
cherché au mauvais endroit, une attente sans fin, et des débris laissés
derrière.

Vous travaillez dans `~/essai-tests`, sur des conteneurs `essai-*`. Le
challenge porte sur `/opt/dsoxlab-images-tester-le-contrat` : n'y touchez pas
pendant le cours.

Page associée : [Tester le contrat d'une image](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/tester-une-image/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-tester-le-contrat
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-tests && cd ~/essai-tests
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🫥 Exercice 1 : un échec avalé par le shell

Trois scripts commencent par `set -e`. Devinez lesquels s'arrêtent :

```bash
printf 'set -e\nverifier() { false; echo "arrive ici"; }\nif verifier; then echo accepte; fi\n' > a.sh
printf 'set -e\nverifier() { local v=$(false); echo "arrive ici"; }\nverifier\n' > b.sh
printf 'set -e\nv=$(false)\necho "arrive ici"\n' > c.sh
for f in a b c; do bash $f.sh; echo "$f: $?"; done
```

```text
arrive ici
accepte
a: 0
arrive ici
b: 0
c: 1
```

Seul le dernier s'arrête. `set -e` est suspendu dans une fonction appelée par
un `if`, un `&&` ou un `||`, et `local` remplace le code de la commande par le
sien. Écrivez le refus vous-même : `commande || { echo "REFUSE"; exit 1; }`.

## 🌐 Exercice 2 : une réponse 500 prise pour un succès

Un service répond toujours 500. Interrogez-le de deux façons :

```bash
docker run -d --init --name essai-web -p 127.0.0.1::8080 "$IMAGE" nc -lk -p 8080 -e printf 'HTTP/1.1 500 Panne\r\nContent-Length: 3\r\nConnection: close\r\n\r\nko\n' > /dev/null
sleep 1
PORT=$(docker port essai-web 8080/tcp | cut -d: -f2)
curl -s "http://127.0.0.1:$PORT/"; echo "sans -f: $?"
curl -fsS "http://127.0.0.1:$PORT/"; echo "avec -f: $?"
docker rm -f essai-web > /dev/null
```

```text
ko
sans -f: 0
curl: (22) The requested URL returned error: 500
avec -f: 22
```

Sans `-f`, `curl` rend 0 dès qu'une réponse arrive, quel que soit son code.
Pour un test, il faut `-f`, et souvent aussi comparer le contenu : un 200 vide
n'est pas un service qui travaille.

## 🔍 Exercice 3 : un message cherché au mauvais endroit

Un programme refuse de démarrer et le dit. Cherchez son message :

```bash
docker run --name essai-dit "$IMAGE" sh -c 'echo "VARIABLE manquante" >&2; exit 1' 2> /dev/null; echo "code: $?"
docker logs essai-dit 2> /dev/null | grep -c manquante
docker logs essai-dit 2>&1 | grep -c manquante
docker rm essai-dit > /dev/null
docker run --rm essai-absente:1 true > /dev/null 2>&1; echo "image absente: $?"
```

```text
code: 1
0
1
image absente: 125
```

Le message est sur la sortie d'erreur : sans `2>&1`, `grep` ne le voit pas et
le test conclut à tort. La dernière ligne montre un autre piège : 125 vient de
Docker, pas de l'image. Un test qui se contente d'un code non nul accepterait
cette panne comme un refus.

## ⏱️ Exercice 4 : une attente sans fin

Attendez la fin de deux conteneurs, dont un qui ne finit pas :

```bash
docker run -d --init --name essai-court "$IMAGE" sh -c 'sleep 1; exit 4' > /dev/null
timeout 5 docker wait essai-court; echo "timeout: $?"
docker run -d --init --name essai-long "$IMAGE" sleep 600 > /dev/null
timeout 2 docker wait essai-long; echo "timeout: $?"
docker rm -f essai-court essai-long > /dev/null
```

```text
4
timeout: 0
timeout: 124
```

`docker wait` affiche le code du conteneur, et `timeout` rend 124 quand il a dû
couper. Ce sont deux informations : « il s'est arrêté avec 4 » et « il ne s'est
pas arrêté ». Lisez les deux.

## 🧹 Exercice 5 : des débris laissés derrière

Un script échoue au milieu, sans puis avec un nettoyage à la sortie. Regardez
aussi un volume anonyme :

```bash
printf 'set -e\ndocker run -d --init --name essai-debris "$IMAGE" sleep 600 > /dev/null\nfalse\ndocker rm -f essai-debris\n' > sans.sh
printf 'set -e\ntrap "docker rm -f essai-propre > /dev/null" EXIT\ndocker run -d --init --name essai-propre "$IMAGE" sleep 600 > /dev/null\nfalse\n' > avec.sh
bash sans.sh; echo "sans: $?, reste $(docker ps -q --filter name=essai-debris | wc -l)"
bash avec.sh; echo "avec: $?, reste $(docker ps -q --filter name=essai-propre | wc -l)"
docker rm -f essai-debris > /dev/null
printf 'FROM %s\nVOLUME /donnees\n' "$IMAGE" > Dockerfile
docker build -q -t essai-tests:vol . > /dev/null
AVANT=$(docker volume ls -q | wc -l)
docker run -d --init --name essai-vol essai-tests:vol sleep 600 > /dev/null
VOLUME=$(docker inspect essai-vol --format '{{(index .Mounts 0).Name}}')
docker rm -f essai-vol > /dev/null; echo "volumes en plus: $(( $(docker volume ls -q | wc -l) - AVANT ))"
docker volume rm "$VOLUME" > /dev/null
```

```text
sans: 1, reste 1
avec: 1, reste 0
volumes en plus: 1
```

Le piège `trap ... EXIT` joue à toute sortie, y compris après un échec, et
conserve le code. Une image qui déclare `VOLUME` crée un volume anonyme que
`docker rm -f` laisse : il faut `docker rm -f -v`.

## 🧹 Nettoyage

```bash
cd ~
docker images 'essai-tests' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-tests
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^essai-'
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
dsoxlab reset images-tester-le-contrat
dsoxlab check images-tester-le-contrat
```

```text
╭─ Résultat : images-tester-le-contrat ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/6 tests      │
╰───────────────────────────────────────╯
```

0 sur 6 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une bonne image, des mauvaises que vous n'avez pas
vues, et un script qui les sépare.

```bash
dsoxlab run images-tester-le-contrat
dsoxlab challenge images-tester-le-contrat
```
