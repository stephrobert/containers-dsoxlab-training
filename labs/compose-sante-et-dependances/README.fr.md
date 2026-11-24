# Attendre la disponibilité, pas seulement un conteneur démarré

La leçon déclare une sonde et fait attendre un service. Ce cours s'intéresse à
ce qui ne marche pas : une condition sans sonde, une sonde qui ne peut pas
s'exécuter, une sonde trop lente, une attente dans un script, et une dépendance
en boucle.

Vous travaillez dans `~/essai-pouls`, sur un projet `essai-pouls`. Le challenge
porte sur le projet `dsoxlab-health` : n'y touchez pas pendant le cours.

Page associée : [Démarrage, disponibilité et santé](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/sante-et-ordre-de-demarrage/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-sante-et-dependances
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
La fonction `sonde` affiche le dernier résultat du journal de la sonde.
**Gardez le même terminal jusqu'au nettoyage** : les variables n'existent que
dans lui.

```bash
mkdir -p ~/essai-pouls && cd ~/essai-pouls
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  base:
    image: ${IMAGE}
    init: true
    command: sleep 600
  client:
    image: ${IMAGE}
    init: true
    command: sleep 600
    depends_on:
      base:
        condition: service_healthy
EOF
sonde() { docker inspect essai-pouls-base-1 --format '{{with index .State.Health.Log 0}}{{.ExitCode}} {{.Output}}{{end}}'; }
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## ❓ Exercice 1 : une condition sans sonde

`client` attend que `base` soit saine, et `base` n'a pas de sonde :

```bash
docker compose config -q; echo "code: $?"
docker compose up -d 2>&1 | grep -o 'has no healthcheck configured'
docker compose ps -a --format '{{.Service}} {{.State}}' | sort
docker compose down
```

```text
code: 0
has no healthcheck configured
base running
client created
```

Le fichier est valide : l'absence de sonde ne se voit qu'au démarrage. `base`
tourne et `client` reste à l'état `created`.

## 🔧 Exercice 2 : une sonde qui ne peut pas s'exécuter

Écrivez une sonde avec un outil absent de l'image, puis une commande complète
dans un seul élément de `CMD` :

```bash
cat > sonde.yaml <<'EOF'
services:
  base:
    image: ${IMAGE}
    init: true
    command: sleep 600
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1"]
      interval: 1s
      retries: 2
EOF
docker compose -f sonde.yaml up -d && sleep 3
sonde | grep -o '^-1\|"curl": executable file not found'
sed -i 's|test: .*|test: ["CMD", "test -f /tmp/pret"]|' sonde.yaml
docker compose -f sonde.yaml up -d && sleep 3
sonde | grep -o '^-1\|stat test -f /tmp/pret: no such file or directory'
```

```text
-1
"curl": executable file not found
-1
stat test -f /tmp/pret: no such file or directory
```

Les deux sondes rendent -1 : la commande n'a jamais été lancée, et
l'application n'y est pour rien. `CMD` attend un mot par élément. Pour une
commande écrite d'un bloc, il faut `CMD-SHELL`, et un shell dans l'image. Lisez
toujours le journal de la sonde avant de chercher une panne.

## 🐢 Exercice 3 : une sonde trop lente

Donnez une seconde à une sonde qui en demande cinq :

```bash
sed -i 's|test: .*|test: ["CMD-SHELL", "sleep 5"]|; s|retries: 2|retries: 1\n      timeout: 1s|' sonde.yaml
docker compose -f sonde.yaml up -d && sleep 4
sonde
docker compose -f sonde.yaml ps --format '{{.Health}}'
```

```text
-1 Health check exceeded timeout (1s)
unhealthy
```

La sonde aurait réussi, mais Docker l'a arrêtée avant. Le journal le dit :
`exceeded timeout`. Un service lent sous charge peut donc devenir `unhealthy`
alors qu'il répond.

## ⏳ Exercice 4 : attendre dans un script

Sondez un fichier, puis demandez à `up` d'attendre, avant et après l'avoir créé
:

```bash
sed -i 's|test: .*|test: ["CMD-SHELL", "test -f /tmp/pret"]|' sonde.yaml
docker compose -f sonde.yaml up -d; echo "code: $?"
docker compose -f sonde.yaml up -d --wait 2>&1 | grep -o 'is unhealthy'
docker compose -f sonde.yaml exec base touch /tmp/pret && sleep 3
docker compose -f sonde.yaml up -d --wait; echo "code: $?"
docker compose -f sonde.yaml down
```

```text
code: 0
is unhealthy
code: 0
```

`up -d` rend 0 dès que le conteneur est lancé. `--wait` attend l'état `healthy`
et échoue sur `unhealthy` : c'est la forme à employer dans un script de
déploiement. `--wait-timeout` borne l'attente.

## 🔄 Exercice 5 : une dépendance en boucle

Faites dépendre deux services l'un de l'autre, puis liez un service aux
redémarrages de sa dépendance :

```bash
cat > boucle.yaml <<'EOF'
services:
  a:
    image: ${IMAGE}
    depends_on: [b]
  b:
    image: ${IMAGE}
    depends_on: [a]
EOF
docker compose -f boucle.yaml config -q
cat > lien.yaml <<'EOF'
services:
  base:
    image: ${IMAGE}
    init: true
    command: sleep 600
  lie:
    image: ${IMAGE}
    init: true
    command: sleep 600
    depends_on:
      base:
        condition: service_started
        restart: true
  libre:
    image: ${IMAGE}
    init: true
    command: sleep 600
    depends_on: [base]
EOF
docker compose -f lien.yaml up -d
debut() { docker inspect "essai-pouls-$1-1" --format '{{.State.StartedAt}}'; }
LIE=$(debut lie); LIBRE=$(debut libre)
docker compose -f lien.yaml restart base
[ "$(debut lie)" = "$LIE" ] && echo "lie: inchange" || echo "lie: redemarre"
[ "$(debut libre)" = "$LIBRE" ] && echo "libre: inchange" || echo "libre: redemarre"
docker compose -f lien.yaml down
```

```text
dependency cycle detected: a -> b -> a
lie: redemarre
libre: inchange
```

Compose refuse la boucle et en donne le chemin. `restart: true` redémarre `lie`
quand Compose redémarre `base`, et `libre` ne bouge pas. Cela vaut pour une
commande Compose, pas pour une base qui tombe d'elle-même.

## 🧹 Nettoyage

```bash
cd ~
rm -r ~/essai-pouls
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
dsoxlab reset compose-sante-et-dependances
dsoxlab check compose-sante-et-dependances
```

```text
╭─ Résultat : compose-sante-et-dependances ─╮
│  0 / 100 pts                              │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests          │
╰───────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un serveur vivant qui n'est pas encore prêt, et un
client qui n'essaie qu'une fois.

```bash
dsoxlab run compose-sante-et-dependances
dsoxlab challenge compose-sante-et-dependances
```
