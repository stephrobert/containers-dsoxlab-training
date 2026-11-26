# Configurer les journaux du démon pour qu'ils survivent au redémarrage

La leçon modifie `daemon.json` avec méthode. Ce cours montre ses angles morts :
ce que la validation attrape et laisse passer, un réglage que le rechargement
n'applique pas, les conteneurs déjà créés, une fusion qui efface, et une erreur
avalée en silence.

Vous travaillez dans `~/essai-demon`. Le challenge porte sur
`/etc/docker/daemon.json` : ce cours le modifie lui aussi, après en avoir gardé
une copie, et le remet en place à la fin.

Page associée : [Administrer le démon et ses contextes](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-configurer-le-demon
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La première commande
garde la configuration actuelle. `pose` écrit la configuration, `relance`
redémarre le démon (`reset-failed` évite que systemd refuse plusieurs
démarrages rapprochés), `cree` affiche les journaux d'un conteneur créé
maintenant. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-demon && cd ~/essai-demon
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sudo test -f /etc/docker/daemon.json && sudo cp -a /etc/docker/daemon.json origine.json
relance() { sudo systemctl reset-failed docker; sudo systemctl restart docker; local r=$?; sleep 3; return $r; }
pose() { echo "$1" | sudo tee /etc/docker/daemon.json > /dev/null; }
cree() { docker create --name "essai-$1" "${@:2}" "$IMAGE" true > /dev/null && docker inspect "essai-$1" --format '{{.HostConfig.LogConfig.Type}} {{json .HostConfig.LogConfig.Config}}'; }
valide() { echo "$1" > essai.json; sudo dockerd --validate --config-file essai.json 2>&1 | tail -1 | grep -oE "invalid character.*|cannot unmarshal [a-z]+|don't match any.*|configuration OK"; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔎 Exercice 1 : ce que la validation attrape

Faites valider six fichiers faux :

```bash
valide '{"log-driver": "json-file",}'
valide '{"log-opts": {"max-file": 2}}'
valide '{"log-drivr": "json-file"}'
valide '{"log-opts": {"max-siz": "10m"}}'
valide '{"log-opts": {"max-size": "10x"}}'
valide '{"log-driver": "inconnu"}'
```

```text
invalid character '}' looking for beginning of object key string
cannot unmarshal number
don't match any configuration option: log-drivr
configuration OK
configuration OK
configuration OK
```

La validation voit la virgule de trop, le nombre sans guillemets et la clé
inconnue. Elle ne lit pas le contenu de `log-opts`, ni le nom du pilote : les
trois derniers fichiers sont déclarés bons. `configuration OK` veut dire « le
fichier se lit », pas « le réglage marche ».

## 🔄 Exercice 2 : un réglage que le rechargement n'applique pas

Appliquez une configuration en redémarrant, changez-la, puis rechargez
seulement :

```bash
pose '{"log-opts": {"max-size": "2m"}, "labels": ["zone=a"]}'
relance
docker info --format '{{.Labels}}'; cree un
pose '{"log-opts": {"max-size": "7m"}, "labels": ["zone=b"]}'
sudo systemctl reload docker; sleep 2
docker info --format '{{.Labels}}'; cree deux
```

```text
[zone=a]
json-file {"max-size":"2m"}
[zone=b]
json-file {"max-size":"2m"}
```

Les deux réglages sont dans le même fichier. Le rechargement a pris l'étiquette
et laissé l'ancienne taille : les valeurs de journal demandent un redémarrage.
Vérifiez chaque réglage par son effet, jamais par le succès de la commande.

## 🧊 Exercice 3 : les conteneurs déjà créés

Redémarrez pour appliquer la nouvelle taille, puis comparez l'ancien conteneur
à trois nouveaux :

```bash
relance
docker inspect essai-un --format '{{json .HostConfig.LogConfig.Config}}'
cree trois
cree quatre --log-opt max-file=3
cree cinq --log-driver local
```

```text
{"max-size":"2m"}
json-file {"max-size":"7m"}
json-file {"max-file":"3","max-size":"7m"}
local {}
```

Le premier garde la valeur de sa création, et le redémarrage n'y change rien.
Une option passée à la création s'ajoute aux valeurs du démon. Changer de
pilote les écarte toutes : le conteneur `cinq` n'a aucune limite déclarée.

## 🧨 Exercice 4 : une fusion qui efface

Ajoutez une clé à une configuration existante, de deux façons :

```bash
python3 - <<'EOF'
import json
avant = {"debug": True, "log-opts": {"labels": "equipe", "max-size": "5m"}}
print(json.dumps({**avant, "log-opts": {"max-file": "2"}}))
print(json.dumps({**avant, "log-opts": {**avant["log-opts"], "max-file": "2"}}))
EOF
```

```text
{"debug": true, "log-opts": {"max-file": "2"}}
{"debug": true, "log-opts": {"labels": "equipe", "max-size": "5m", "max-file": "2"}}
```

Remplacer `log-opts` en entier perd `labels` et `max-size`, sans aucune erreur.
Il faut fusionner à l'intérieur. Comparez toujours l'ancien et le nouveau
fichier avant de redémarrer.

## 🤐 Exercice 5 : une erreur avalée en silence

Cassez le fichier et rechargez, puis posez une taille impossible et redémarrez
:

```bash
pose '{"labels":,}'
sudo systemctl reload docker; echo "reload: $?"; sleep 2
docker info --format '{{.Labels}}'
sudo journalctl -u docker -n 20 -o cat --no-pager | grep -o 'Error reloading configuration' | tail -1
pose '{"log-opts": {"max-size": "10x"}}'
relance; echo "restart: $?"
docker run --rm "$IMAGE" true 2>&1 | grep -o "invalid suffix.*"
```

```text
reload: 0
[zone=b]
Error reloading configuration
restart: 0
invalid suffix: 'x'
```

Le rechargement rend 0, garde l'ancienne configuration et n'écrit l'erreur que
dans le journal du service. Le redémarrage réussit avec une taille impossible,
et c'est le premier conteneur lancé qui échoue. Terminez toujours par un
conteneur d'essai.

## 🧹 Nettoyage

```bash
cd ~
if [ -f ~/essai-demon/origine.json ]; then sudo cp -a ~/essai-demon/origine.json /etc/docker/daemon.json; else sudo rm /etc/docker/daemon.json; fi
relance
docker rm -f essai-un essai-deux essai-trois essai-quatre essai-cinq > /dev/null
rm -rf ~/essai-demon
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
dsoxlab reset docker-configurer-le-demon
dsoxlab check docker-configurer-le-demon
```

```text
╭─ Résultat : docker-configurer-le-demon ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests        │
╰─────────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : des journaux bornés pour tous les nouveaux
conteneurs, sans perdre un réglage.

```bash
dsoxlab run docker-configurer-le-demon
dsoxlab challenge docker-configurer-le-demon
```
