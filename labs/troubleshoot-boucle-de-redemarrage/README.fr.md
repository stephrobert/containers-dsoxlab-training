# Une boucle de redémarrage, et deux issues

La leçon explique les politiques de redémarrage et la réparation d'une boucle.
Ce cours ajoute cinq gestes d'enquête : mesurer la cadence des relances,
reconnaître une boucle sans échec, isoler les journaux du dernier essai,
examiner un conteneur qui ne reste pas en marche, et plafonner les relances sans
le recréer.

Vous travaillez sur `essai-boucle` et `essai-zero`. Le challenge porte sur les
conteneurs `appli-*` : n'y touchez pas pendant le cours.

Page associée : [Lire un échec de démarrage Docker : codes et boucles](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run troubleshoot-boucle-de-redemarrage
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. Lancez deux conteneurs
qui bouclent. La fonction `attendre` patiente jusqu'au moment où un conteneur
est entre deux essais. **Gardez le même terminal jusqu'au nettoyage.**

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
DEBUT=$(date +%s)
docker run -d --name essai-boucle --restart always "$IMAGE" sh -c 'echo "essai $(date +%T)"; echo reste > /trace.txt; exit 1' > /dev/null
docker run -d --name essai-zero --restart always "$IMAGE" sh -c 'echo tache finie; exit 0' > /dev/null
attendre() { until [ "$(docker container inspect "$1" --format '{{.State.Restarting}}')" = true ]; do sleep 0.2; done; }
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les heures et les nombres d'essais seront différents chez vous.

## ⏱️ Exercice 1 : mesurer la cadence des relances

Chaque fin du programme produit un événement `die`. Calculez l'écart en secondes
entre deux fins :

```bash
sleep 12
docker events --since "$DEBUT" --until "$(date +%s)" --filter container=essai-boucle --filter event=die --format '{{.Time}}' | awk 'NR>1 {printf "%d ", $1-avant} {avant=$1} END {print ""}'
docker container inspect essai-boucle --format 'relances={{.RestartCount}}'
```

```text
0 1 0 1 2 3
relances=7
```

Les écarts s'allongent : Docker attend de plus en plus longtemps. Cette trace
sert aussi après coup, pour dater le début d'une boucle.

## 0️⃣ Exercice 2 : une boucle sans échec

Le second conteneur boucle aussi. Regardez son code :

```bash
attendre essai-zero
docker ps -a --filter name=essai-zero --format '{{.Names}} {{.Status}}'
docker logs --tail 1 essai-zero
```

```text
essai-zero Restarting (0) 4 seconds ago
tache finie
```

`Restarting (0)` : le programme réussit et se termine, et la politique `always`
le relance. Il n'y a rien à réparer dans le programme. C'est la politique qui ne
convient pas à une tâche qui a une fin.

## 📜 Exercice 3 : les journaux du dernier essai

Les journaux d'un conteneur en boucle mélangent tous les essais. Comptez les
lignes, puis ne gardez que la dernière, datée :

```bash
docker logs essai-boucle | wc -l
docker logs --tail 1 --timestamps essai-boucle
```

```text
7
2026-11-24T09:53:55.490754079Z essai 09:53:55
```

`--timestamps` date la ligne, en temps universel. Avec `--since` et cette date,
vous isolez les lignes d'un seul essai quand le programme en écrit plusieurs.

## 🔬 Exercice 4 : examiner un conteneur qui ne tient pas

Vous voulez voir les fichiers du conteneur, mais il ne reste pas en marche :

```bash
attendre essai-boucle
docker exec essai-boucle cat /trace.txt
docker diff essai-boucle
docker commit essai-boucle essai-autopsie:1 > /dev/null
docker run --rm essai-autopsie:1 cat /trace.txt
```

```text
Error response from daemon: Container 764de12d158c610dd7c3e4511ec284da99c6cb6955e3505479d6cd692ecaf443 is restarting, wait until the container is running
A /trace.txt
reste
```

`docker exec` est refusé entre deux essais. `docker diff` liste quand même ce que
le programme a écrit. `docker commit` fige les fichiers du conteneur dans une
image, que vous ouvrez avec une autre commande. Le conteneur d'origine continue
de boucler, intact.

## 🛑 Exercice 5 : plafonner sans recréer

`docker update` change la politique d'un conteneur existant. Donnez un plafond
aux deux, attendez, puis redémarrez `essai-boucle` :

```bash
docker update --restart on-failure:2 essai-zero essai-boucle
sleep 20
docker ps -a --filter name=^essai- --format '{{.Names}} {{.Status}}'
docker start essai-boucle > /dev/null
sleep 6
docker container inspect essai-boucle --format 'relances={{.RestartCount}} statut={{.State.Status}} code={{.State.ExitCode}}'
```

```text
essai-zero
essai-boucle
essai-zero Exited (0) 19 seconds ago
essai-boucle Exited (1) 19 seconds ago
relances=2 statut=exited code=1
```

Les deux se sont arrêtés, pour deux raisons : `essai-zero` a rendu 0, que
`on-failure` ne relance pas, et `essai-boucle` avait déjà dépassé son plafond.
Après `docker start`, le compteur est reparti de zéro et s'est arrêté à 2. La
panne, elle, est toujours là : la boucle a cessé, rien n'est réparé.

## 🧹 Nettoyage

```bash
docker rm -f essai-boucle essai-zero > /dev/null
docker rmi essai-autopsie:1 > /dev/null
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
dsoxlab reset troubleshoot-boucle-de-redemarrage
dsoxlab check troubleshoot-boucle-de-redemarrage
```

```text
╭─ Résultat : troubleshoot-boucle-de-redemarrage ─╮
│  0 / 100 pts                                    │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests                │
╰─────────────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : lire deux conteneurs en échec, lever leur cause, et
laisser le moteur relancer celui qui boucle sans lui retirer sa politique.

```bash
dsoxlab run troubleshoot-boucle-de-redemarrage
dsoxlab challenge troubleshoot-boucle-de-redemarrage
```
