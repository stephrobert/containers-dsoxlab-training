# Deux variantes d'un même socle, et aucun montage de dev en déploiement

La leçon assemble un socle et ses variantes, et lit la configuration effective.
Ce cours ajoute cinq situations : un chemin relatif qui change de sens, une
comparaison entre variantes, une faute de nom, un service perdu en dérivant, et
un service sous profil qui survit à l'arrêt.

Vous travaillez dans `~/essai-formes`, sur un projet `essai-formes`. Le
challenge porte sur `/opt/lab-variantes` : n'y touchez pas pendant le cours.

Page associée : [Développement et déploiement : variantes explicites](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/variantes-de-deploiement/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-profils-et-variantes
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Écrivez un socle, et une variante rangée dans un sous-répertoire. **Gardez le
même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-formes && cd ~/essai-formes
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
mkdir -p variantes donnees
cat > compose.yaml <<'EOF'
services:
  service:
    image: ${IMAGE}
    init: true
    command: sleep 600
  aide:
    image: ${IMAGE}
    init: true
    command: sleep 600
    profiles: ["aide"]
EOF
cat > variantes/atelier.yaml <<'EOF'
services:
  service:
    volumes:
      - ./donnees:/donnees
EOF
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🧭 Exercice 1 : un chemin relatif qui change de sens

Assemblez les deux fichiers dans les deux ordres et lisez la source du montage
:

```bash
docker compose -f compose.yaml -f variantes/atelier.yaml config | grep 'source:' | sed "s|$HOME|~|"
docker compose -p essai-formes -f variantes/atelier.yaml -f compose.yaml config | grep 'source:' | sed "s|$HOME|~|"
```

```text
        source: ~/essai-formes/donnees
        source: ~/essai-formes/variantes/donnees
```

Les chemins relatifs de tous les fichiers partent du répertoire du premier
`-f`. Dans le second ordre, le montage vise un répertoire qui n'existe pas, et
Compose ne dit rien.

## 🔍 Exercice 2 : comparer deux variantes

Comparez les configurations effectives, pas les fichiers :

```bash
docker compose -f compose.yaml config > base.txt
docker compose -f compose.yaml -f variantes/atelier.yaml config > atelier.txt
diff base.txt atelier.txt | sed "s|$HOME|~|"
```

```text
10a11,15
>     volumes:
>       - type: bind
>         source: ~/essai-formes/donnees
>         target: /donnees
>         bind: {}
```

La différence entre les deux variantes tient en cinq lignes. Cette comparaison,
rejouée avant chaque livraison, montre tout ce qu'une variante ajoute, y
compris ce que personne ne cherchait.

## ✏️ Exercice 3 : une faute dans le nom du service

Écrivez une variante qui se trompe de nom, sans puis avec une image :

```bash
printf 'services:\n  servise:\n    restart: always\n' > faute.yaml
docker compose -f compose.yaml -f faute.yaml config -q
printf '    image: alpine\n' >> faute.yaml
docker compose -f compose.yaml -f faute.yaml config -q; echo "code: $?"
docker compose -f compose.yaml -f faute.yaml config --services | sort
```

```text
service "servise" has neither an image nor a build context specified: invalid compose project
code: 0
service
servise
```

Un nom inconnu ajoute un service. Sans image, Compose le refuse ; avec une
image, il l'accepte, et `service` n'a pas reçu `restart`. Relisez la liste des
services après chaque fusion.

## 🧬 Exercice 4 : un service perdu en dérivant

Dérivez le socle par `extends`, puis par `include`, et demandez les services du
profil :

```bash
cat > par-extends.yaml <<'EOF'
services:
  service:
    extends:
      file: compose.yaml
      service: service
EOF
printf 'include:\n  - compose.yaml\n' > par-include.yaml
docker compose -f par-extends.yaml --profile aide config --services | sort
echo '--'
docker compose -f par-include.yaml --profile aide config --services | sort
echo '--'
docker compose -f compose.yaml -f variantes/atelier.yaml --profile aide config --services | sort
```

```text
service
--
aide
service
--
aide
service
```

`extends` reprend un service nommé, et lui seul : `aide` a disparu. `include`
et la liste de `-f` reprennent le fichier entier. Choisissez la méthode selon
ce qui doit suivre.

## 👻 Exercice 5 : un service sous profil qui survit à l'arrêt

Démarrez avec le profil, puis arrêtez sans lui, de deux façons :

```bash
docker compose --profile aide up -d
docker compose down
docker ps --format '{{.Names}}' | grep essai
docker compose -p essai-formes down
docker ps --format '{{.Names}}' | grep -c essai
```

```text
essai-formes-aide-1
0
```

Le premier `down` lit le fichier, où `aide` est éteint, et le laisse en marche.
Avec `-p`, Compose retrouve les conteneurs par leur étiquette de projet et
retire aussi `aide`. Redonner `--profile aide` à l'arrêt fonctionne également.

## 🧹 Nettoyage

```bash
cd ~
rm -r ~/essai-formes
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
dsoxlab reset compose-profils-et-variantes
dsoxlab check compose-profils-et-variantes
```

```text
╭─ Résultat : compose-profils-et-variantes ─╮
│  0 / 100 pts                              │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests          │
╰───────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un socle intouchable, deux variantes à en tirer, et
la bonne à laisser en service.

```bash
dsoxlab run compose-profils-et-variantes
dsoxlab challenge compose-profils-et-variantes
```
