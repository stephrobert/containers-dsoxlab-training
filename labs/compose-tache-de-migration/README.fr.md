# Conditionner le démarrage à une migration réussie

La leçon fait attendre une application derrière une migration. Ce cours ajoute
cinq situations : deux tâches en chaîne, une tâche rejouée à chaque démarrage,
un échec que l'on contourne sans le voir, un code de sortie perdu, et une tâche
interrompue à mi-chemin.

Vous travaillez dans `~/essai-taches`, sur un projet `essai-taches` dont les
tâches écrivent dans un journal. Le challenge porte sur le projet
`dsoxlab-migration` : n'y touchez pas pendant le cours.

Page associée : [Démarrage, disponibilité et santé](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/sante-et-ordre-de-demarrage/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-tache-de-migration
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
La variable `CODE_UN` choisira le code de sortie de la première tâche. **Gardez
le même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-taches && cd ~/essai-taches
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
x-tache: &tache
  image: ${IMAGE}
  init: true
  environment:
    CODE_UN: ${CODE_UN:-0}
  volumes:
    - journal:/journal
services:
  un:
    <<: *tache
    command: ["sh", "-c", "echo un >> /journal/suivi; exit $$CODE_UN"]
  deux:
    <<: *tache
    command: ["sh", "-c", "echo deux >> /journal/suivi"]
    depends_on:
      un:
        condition: service_completed_successfully
  appli:
    <<: *tache
    command: ["sleep", "600"]
    depends_on:
      deux:
        condition: service_completed_successfully
volumes:
  journal:
EOF
etats() { docker compose ps -a --format '{{.Service}} {{.State}} {{.ExitCode}}' | sort; }
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## ⛓️ Exercice 1 : deux tâches en chaîne

Démarrez et lisez l'ordre des écritures :

```bash
docker compose up -d
docker compose exec appli cat /journal/suivi
etats
```

```text
un
deux
appli running 0
deux exited 0
un exited 0
```

Chaque tâche attend la fin réussie de la précédente, et `appli` attend la
dernière. Une tâche terminée reste visible avec `ps -a`, avec son code.

## 🔁 Exercice 2 : une tâche rejouée à chaque démarrage

Relancez sans rien changer au fichier :

```bash
AVANT=$(docker inspect essai-taches-appli-1 --format '{{.Id}}')
docker compose up -d
docker compose exec appli cat /journal/suivi
[ "$(docker inspect essai-taches-appli-1 --format '{{.Id}}')" = "$AVANT" ] && echo "appli: inchangee"
```

```text
un
deux
un
deux
appli: inchangee
```

Les deux tâches ont tourné une seconde fois, et `appli` n'a pas bougé. Une
migration doit donc supporter d'être rejouée à chaque déploiement.

## 🕳️ Exercice 3 : un échec contourné

Faites échouer la première tâche, puis démarrez `appli` de trois façons :

```bash
docker compose down -v
export CODE_UN=4
docker compose up -d 2>&1 | grep -o "didn't complete successfully.*"
etats
docker compose start appli 2>&1 | grep -o "didn't complete successfully.*"
docker compose up -d --no-deps appli; echo "code: $?"
etats
docker compose down -v
```

```text
didn't complete successfully: exit 4
appli created 0
deux created 0
un exited 4
didn't complete successfully: exit 4
code: 0
appli running 0
deux created 0
un exited 4
```

`up` et `start` refusent. `--no-deps` démarre `appli` sans regarder ses
dépendances, sans un avertissement : l'application tourne sur un schéma qui n'a
pas été migré. Un `docker start` du conteneur ferait de même. La condition
protège le chemin normal, pas les raccourcis.

## 🔢 Exercice 4 : un code de sortie perdu

Lancez la tâche en échec seule, de trois façons, et lisez le code rendu :

```bash
docker compose up -d un; echo "up -d: $?"
docker compose up --exit-code-from un un > /dev/null 2>&1; echo "exit-code-from: $?"
docker compose run --rm un > /dev/null 2>&1; echo "run: $?"
docker compose down -v
```

```text
up -d: 0
exit-code-from: 4
run: 4
```

`up -d` rend 0 : il a lancé le conteneur, et n'attend pas sa fin. Dans un
script, employez `run --rm`, ou `--exit-code-from`, qui rendent le code de la
tâche.

## ✂️ Exercice 5 : une tâche interrompue à mi-chemin

Deux tâches écrivent un résultat en deux temps. Interrompez-les au milieu :

```bash
cat > partiel.yaml <<'EOF'
x-tache: &tache
  image: ${IMAGE}
  init: true
  volumes:
    - resultat:/resultat
services:
  directe:
    <<: *tache
    command: ["sh", "-ec", "echo a > /resultat/direct; ${MILIEU:-true}; echo b >> /resultat/direct"]
  sure:
    <<: *tache
    command: ["sh", "-ec", "echo a > /resultat/sur.tmp; ${MILIEU:-true}; echo b >> /resultat/sur.tmp; mv /resultat/sur.tmp /resultat/sur"]
volumes:
  resultat:
EOF
MILIEU=false docker compose -f partiel.yaml run --rm directe > /dev/null 2>&1; echo "directe: $?"
MILIEU=false docker compose -f partiel.yaml run --rm sure > /dev/null 2>&1; echo "sure: $?"
docker compose -f partiel.yaml run --rm sure ls /resultat
docker compose -f partiel.yaml run --rm sure
docker compose -f partiel.yaml run --rm sure cat /resultat/sur
docker compose -f partiel.yaml down -v
```

```text
directe: 1
sure: 1
direct
sur.tmp
a
b
```

Les deux tâches échouent, mais la première laisse un fichier `direct` incomplet
que l'application prendrait pour bon. La seconde travaille à côté et renomme à
la fin : le résultat existe en entier ou pas du tout. Une base de données offre
la même garantie avec une transaction.

## 🧹 Nettoyage

```bash
cd ~
unset CODE_UN
rm -r ~/essai-taches
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
0
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset compose-tache-de-migration
dsoxlab check compose-tache-de-migration
```

```text
╭─ Résultat : compose-tache-de-migration ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests        │
╰─────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une vraie base, une migration à rejouer, et une
application qui doit l'attendre.

```bash
dsoxlab run compose-tache-de-migration
dsoxlab challenge compose-tache-de-migration
```
