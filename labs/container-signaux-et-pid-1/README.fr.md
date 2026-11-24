# Qui est PID 1 décide si votre conteneur s'arrête ou se fait tuer

La leçon montre pourquoi un PID 1 sans gestionnaire ignore SIGTERM, et comment
`exec` ou `--init` règlent le problème. Ce cours ajoute cinq gestes : lire dans
le noyau si un PID 1 traite SIGTERM, changer le signal d'arrêt, envoyer un
signal sans arrêter le conteneur, relayer le signal depuis un script qui doit
rester en place, et repérer les processus zombies.

Vous travaillez dans `~/essai-signaux`, sur des conteneurs `essai-*`. Le
challenge porte sur une autre application, dans `/opt/lab-signaux`.

Page associée : [Cycle de vie d'un conteneur, PID 1 et arrêt propre](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cycle-de-vie-et-signaux/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-signaux-et-pid-1
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : la variable `IMAGE` n'existe que dans lui.

```bash
mkdir -p ~/essai-signaux && cd ~/essai-signaux
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026.

## 🔬 Exercice 1 : lire si le PID 1 traite SIGTERM

Chronométrer un arrêt demande d'arrêter le conteneur. Le noyau donne la réponse
sur un conteneur en marche : la ligne `SigCgt` de `/proc/1/status` est un masque
des signaux pour lesquels le processus a un gestionnaire. SIGTERM porte le
numéro 15, donc le bit 14, puisque les bits se comptent à partir de 0 :

```bash
docker run -d --name essai-sourd "$IMAGE" sleep 600 > /dev/null
docker run -d --name essai-attentif "$IMAGE" sh -c 'trap "exit 0" TERM; while :; do sleep 1; done' > /dev/null
sleep 1
for c in essai-sourd essai-attentif; do
  M=$(docker exec $c awk '/^SigCgt/ {print $2}' /proc/1/status)
  echo "$c SigCgt=$M SIGTERM=$(( (0x$M >> 14) & 1 ))"
done
```

```text
essai-sourd SigCgt=0000000000000000 SIGTERM=0
essai-attentif SigCgt=0000000000014002 SIGTERM=1
```

`sleep` n'a aucun gestionnaire : son masque est nul, et il ignorera SIGTERM. Le
second shell a le bit 14 à 1 : il le traitera. Vous savez maintenant prévoir un
arrêt de dix secondes sans le provoquer.

## 🎚️ Exercice 2 : changer le signal d'arrêt

Certaines applications s'arrêtent sur un autre signal que SIGTERM. Celle-ci
n'intercepte que SIGINT. Lancez-la deux fois, la seconde avec `--stop-signal` :

```bash
docker run -d --name essai-int "$IMAGE" sh -c 'trap "echo int-recu; exit 0" INT; while :; do sleep 1; done' > /dev/null
docker run -d --name essai-int-regle --stop-signal SIGINT "$IMAGE" sh -c 'trap "echo int-recu; exit 0" INT; while :; do sleep 1; done' > /dev/null
sleep 1
for c in essai-int essai-int-regle; do
  docker stop --timeout 3 $c > /dev/null
  docker container inspect $c --format "$c StopSignal={{.Config.StopSignal}} code={{.State.ExitCode}}"
  docker logs $c
done
```

```text
essai-int StopSignal= code=137
essai-int-regle StopSignal=SIGINT code=0
int-recu
```

Le premier conteneur a reçu SIGTERM, l'a ignoré et a été tué : code 137, aucun
journal. Le second a reçu SIGINT : il a écrit sa ligne et rendu 0. Avant de
modifier une application, vérifiez donc quel signal elle attend.

## 🔁 Exercice 3 : un signal qui n'arrête pas

Le mot `kill` trompe : `docker kill` envoie SIGKILL par défaut, mais
`--signal` en choisit un autre. Beaucoup de services relisent leur configuration
sur SIGHUP. Envoyez-le :

```bash
docker run -d --name essai-relecture "$IMAGE" sh -c 'trap "echo relecture" HUP; trap "exit 0" TERM; while :; do sleep 1; done' > /dev/null
sleep 1
docker kill --signal HUP essai-relecture
sleep 2
docker logs essai-relecture
docker container inspect essai-relecture --format 'etat={{.State.Status}}'
```

```text
essai-relecture
relecture
etat=running
```

L'application a traité le signal et le conteneur tourne toujours.

## 🤝 Exercice 4 : relayer le signal depuis un script

`exec` remplace le script par l'application : rien ne peut plus s'exécuter
après elle. Si le script doit faire le ménage à la fin, il doit rester en place
et relayer lui-même le signal :

```bash
cat > app.sh <<'EOF'
#!/bin/sh
trap 'echo app-recu; exit 0' TERM
echo app-demarre
while :; do sleep 1; done
EOF
cat > relais.sh <<'EOF'
#!/bin/sh
/relais/app.sh &
ENFANT=$!
trap "kill -TERM $ENFANT" TERM
wait $ENFANT
wait $ENFANT
CODE=$?
echo menage-fait
exit $CODE
EOF
chmod +x app.sh relais.sh
docker run -d --name essai-relais -v "$PWD:/relais:ro" "$IMAGE" /relais/relais.sh > /dev/null
sleep 1
docker exec essai-relais cat /proc/1/comm
docker stop essai-relais > /dev/null
docker container inspect essai-relais --format 'code={{.State.ExitCode}}'
docker logs essai-relais
```

```text
relais.sh
code=0
app-demarre
app-recu
menage-fait
```

Le PID 1 est resté `relais.sh`. Son `trap` a transmis SIGTERM à l'application,
qui a écrit `app-recu`, puis le script a fini par `menage-fait` avec le code de
l'application. Il faut deux `wait` : le signal interrompt le premier, et le
second attend la vraie fin. Ce montage ne convient pas au challenge, qui demande
que l'application soit elle-même le PID 1.

## 🧟 Exercice 5 : les processus zombies

Un processus terminé reste dans la table des processus, à l'état `Z`, tant que
son parent n'a pas lu son code de sortie. Quand le parent disparaît, c'est le PID 1
qui hérite de ce travail. Comparez un PID 1 qui ne le fait pas et un conteneur
lancé avec `--init` :

```bash
docker run -d --name essai-zombies "$IMAGE" sh -c 'for i in 1 2 3; do (sleep 1 &); done; exec sleep 600' > /dev/null
docker run -d --init --name essai-init "$IMAGE" sh -c 'for i in 1 2 3; do (sleep 1 &); done; exec sleep 600' > /dev/null
sleep 3
docker exec essai-zombies ps -o pid,ppid,stat,comm
docker exec essai-init ps -o pid,ppid,stat,comm
```

```text
PID   PPID  STAT COMMAND
    1     0 S    sleep
    8     1 Z    sleep
   10     1 Z    sleep
   12     1 Z    sleep
   13     0 R    ps
PID   PPID  STAT COMMAND
    1     0 S    docker-init
    7     1 S    sleep
   14     0 R    ps
```

Sans init, trois `sleep` terminés restent à l'état `Z`, rattachés au PID 1. Avec
`docker-init`, ils ont disparu. Une application qui lance beaucoup de processus
peut ainsi remplir sa limite de processus avec des zombies.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-sourd essai-attentif essai-int essai-int-regle essai-relecture essai-relais essai-zombies essai-init > /dev/null
rm -r ~/essai-signaux
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
dsoxlab reset container-signaux-et-pid-1
dsoxlab check container-signaux-et-pid-1
```

```text
╭─ Résultat : container-signaux-et-pid-1 ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests        │
╰─────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : constater un arrêt en 137, puis corriger l'image pour
que l'application reçoive le signal, sans supprimer la préparation.

```bash
dsoxlab run container-signaux-et-pid-1
dsoxlab challenge container-signaux-et-pid-1
```
