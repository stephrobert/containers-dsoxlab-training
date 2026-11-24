# Accorder un secret Compose uniquement à son consommateur

La leçon accorde un secret fichier à un service, puis le remplace. Ce cours
ajoute cinq situations : un secret pris dans l'environnement du poste, un nom
différent dans le conteneur, un retour à la ligne de trop, deux erreurs de
déclaration, et une copie qui finit dans une image.

Vous travaillez dans `~/essai-cles`, sur un projet `essai-cles`, avec des
valeurs de démonstration. Le challenge porte sur `/opt/lab-compose-secret` :
n'y touchez pas pendant le cours.

Page associée : [Injecter les secrets, et connaître leurs limites](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/secrets/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-secrets
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Écrivez un service qui reçoit un secret. **Gardez le même terminal jusqu'au
nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-cles && cd ~/essai-cles
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  caisse:
    image: ${IMAGE}
    init: true
    command: sleep 600
    secrets:
      - source: cle
        target: cle_de_caisse
secrets:
  cle:
    file: ./cle.txt
EOF
printf 'valeur-demo\n' > cle.txt
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🏷️ Exercice 1 : un autre nom dans le conteneur

Démarrez et cherchez le secret sous ses deux noms :

```bash
docker compose up -d
docker compose exec caisse ls /run/secrets
docker compose exec caisse cat /run/secrets/cle
```

```text
cle_de_caisse
cat: can't open '/run/secrets/cle': No such file or directory
```

La forme longue sépare `source`, le nom du bloc du bas, et `target`, le nom du
fichier que l'application lit. Seul le second existe dans le conteneur.

## ↩️ Exercice 2 : un retour à la ligne de trop

Comptez les octets que le conteneur reçoit, puis comparez deux façons de lire
la valeur :

```bash
printf 'valeur-demo' | wc -c
docker compose exec caisse sh -c 'wc -c < /run/secrets/cle_de_caisse'
docker compose exec caisse sh -c 'printf valeur-demo | cmp - /run/secrets/cle_de_caisse'
docker compose exec caisse sh -c '[ "$(cat /run/secrets/cle_de_caisse)" = valeur-demo ] && echo egal'
```

```text
11
12
cmp: EOF on -
egal
```

Le fichier contient un octet de plus : le retour à la ligne. Un shell le retire
en lisant, un programme qui lit tous les octets le garde, et l'authentification
échoue avec une valeur qui paraît juste. Écrivez le secret avec `printf`, sans
`\n`, ou vérifiez que l'application retire ce caractère.

## 🚫 Exercice 3 : deux erreurs de déclaration

Accordez un secret que personne ne déclare, puis déclarez un fichier absent :

```bash
sed 's/source: cle$/source: clef/' compose.yaml > faute.yaml
docker compose -f faute.yaml config -q 2>&1 | grep -o 'service.*'
sed 's/cle.txt/rien.txt/' compose.yaml > absent.yaml
docker compose -f absent.yaml config -q; echo "code: $?"
docker compose -p essai-absent -f absent.yaml up -d 2>&1 | grep -o 'bind source path does not exist'
docker compose -p essai-absent -f absent.yaml down
```

```text
service "caisse" refers to undefined secret clef: invalid compose project
code: 0
bind source path does not exist
```

`config` refuse un nom inconnu, mais ne vérifie pas que le fichier existe : il
rend 0. L'erreur vient au démarrage, et le réseau du projet a déjà été créé.
D'où le `down`.

## 🌍 Exercice 4 : un secret pris dans l'environnement

Prenez la valeur dans une variable du poste, puis cherchez-la là où elle ne
devrait pas être :

```bash
sed 's|file: ./cle.txt|environment: CLE_POSTE|' compose.yaml > env.yaml
docker compose -p essai-env -f env.yaml up -d 2>&1 | grep -o 'environment variable.*'
export CLE_POSTE=autre-demo
docker compose -p essai-env -f env.yaml up -d
docker inspect essai-env-caisse-1 | grep -c autre-demo
docker export essai-env-caisse-1 | grep -a -c autre-demo
docker export essai-cles-caisse-1 | grep -a -c valeur-demo
docker compose -p essai-env -f env.yaml down
unset CLE_POSTE
```

```text
environment variable "CLE_POSTE" required by secret "essai-env_cle" is not set
0
1
0
```

La valeur est absente de l'inspection, mais présente dans l'export : faute de
fichier à monter, Compose l'a copiée dans la couche d'écriture du conteneur.
Avec un fichier, l'export ne contient rien. La source change donc l'endroit où
la valeur se retrouve sur le disque.

## 📸 Exercice 5 : une copie qui finit dans une image

Faites comme un script de démarrage qui recopie le secret, puis figez le
conteneur en image :

```bash
docker compose exec caisse sh -c 'cat /run/secrets/cle_de_caisse > /tmp/copie'
docker commit essai-cles-caisse-1 essai-cles:fuite > /dev/null
docker run --rm essai-cles:fuite cat /tmp/copie
docker run --rm essai-cles:fuite cat /run/secrets/cle_de_caisse
docker rmi -f essai-cles:fuite > /dev/null
```

```text
valeur-demo
```

Le montage n'a pas suivi : le fichier est présent mais vide. La copie, elle,
est partie dans l'image, lisible par tous ceux qui la reçoivent. Un secret
monté ne protège pas d'une application qui le recopie.

## 🧹 Nettoyage

```bash
cd ~
docker compose -f ~/essai-cles/compose.yaml down
rm -r ~/essai-cles
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
dsoxlab reset compose-secrets
dsoxlab check compose-secrets
```

```text
╭─── Résultat : compose-secrets ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un jeton, un seul service qui le lit, et une valeur à
remplacer.

```bash
dsoxlab run compose-secrets
dsoxlab challenge compose-secrets
```
