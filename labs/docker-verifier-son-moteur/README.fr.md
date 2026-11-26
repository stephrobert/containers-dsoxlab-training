# Le moteur fonctionne-t-il vraiment ? Quatre réponses, pas une

La leçon installe Docker et contrôle l'installation. Ce cours apprend à lire
une panne avant de la réparer, sur des objets d'essai : deux erreurs qui se
ressemblent, un service démarré mais pas activé, un service bloqué, un groupe
pas encore pris en compte, et un fichier de configuration faux.

Sur cette machine, le moteur Docker est en panne exprès : c'est l'objet du
challenge. **Ne le réparez pas pendant le cours.** Vous travaillez sur un
service `essai-veille` et un compte `essai-compte`, créés puis supprimés ici.

Page associée : [Installer Docker Engine 29 et prouver qu'il fonctionne](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/installation/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-verifier-son-moteur
```

Vous êtes connecté à `docker.lab`. La dernière commande interroge seulement le
client. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-moteur && cd ~/essai-moteur
docker --version | cut -d, -f1
```

```text
Docker version 29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📞 Exercice 1 : deux erreurs qui se ressemblent

Visez un socket qui n'existe pas, puis un socket qui existe mais que votre
compte n'a pas le droit d'ouvrir :

```bash
export DOCKER_HOST=unix:///tmp/essai-absent.sock
docker ps 2>&1 | grep -oE 'permission denied|[Cc]annot connect|failed to connect' | head -1
cat > prise.py <<'EOF'
import os, socket, time
s = socket.socket(socket.AF_UNIX)
s.bind("/tmp/essai-prise.sock")
os.chmod("/tmp/essai-prise.sock", 0o600)
s.listen()
time.sleep(60)
EOF
sudo python3 prise.py & sleep 1
export DOCKER_HOST=unix:///tmp/essai-prise.sock
docker ps 2>&1 | grep -oE 'permission denied|[Cc]annot connect|failed to connect' | head -1
sudo pkill -f '^python3 prise.py'; sudo rm -f /tmp/essai-prise.sock; unset DOCKER_HOST
```

```text
failed to connect
permission denied
```

La première erreur dit que personne n'écoute : regardez le service. La seconde
dit que la porte existe et vous est fermée : regardez les droits. Réinstaller
le paquet ne change ni l'une ni l'autre. `docker --version`, lui, répond
toujours : il n'interroge que le client.

## 🔁 Exercice 2 : démarré, mais pas activé

Créez un service, démarrez-le, puis posez les deux questions :

```bash
printf '[Service]\nExecStart=/bin/sleep 900\n[Install]\nWantedBy=multi-user.target\n' | sudo tee /etc/systemd/system/essai-veille.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl start essai-veille
systemctl is-active essai-veille; systemctl is-enabled essai-veille
sudo systemctl enable -q essai-veille && sudo systemctl stop essai-veille
systemctl is-active essai-veille; systemctl is-enabled essai-veille
ls -l /etc/systemd/system/multi-user.target.wants/essai-veille.service | grep -o '> .*'
```

```text
active
disabled
inactive
enabled
> /etc/systemd/system/essai-veille.service
```

Les deux états sont indépendants. Activer pose un lien que le démarrage de la
machine suivra ; cela ne lance rien tout de suite. `enable --now` fait les deux
gestes.

## 🚧 Exercice 3 : un service bloqué

Masquez le service, essayez de le démarrer, puis donnez-lui un programme qui
n'existe pas :

```bash
sudo rm /etc/systemd/system/multi-user.target.wants/essai-veille.service /etc/systemd/system/essai-veille.service
sudo systemctl daemon-reload && sudo systemctl mask -q essai-veille
sudo systemctl start essai-veille 2>&1 | grep -o 'is masked'
systemctl is-enabled essai-veille
sudo systemctl unmask -q essai-veille
printf '[Service]\nExecStart=/usr/bin/programme-absent\n' | sudo tee /etc/systemd/system/essai-veille.service > /dev/null
sudo systemctl daemon-reload && sudo systemctl start essai-veille; sleep 1
systemctl is-active essai-veille
systemctl show essai-veille -p Result -p ExecMainStatus
sudo journalctl -u essai-veille -n 20 --no-pager -o cat | grep -o 'Unable to locate executable.*' | head -1
```

```text
Unit essai-veille.service does not exist, proceeding anyway.
is masked
masked
failed
Result=exit-code
ExecMainStatus=203
Unable to locate executable '/usr/bin/programme-absent': No such file or directory
```

Un service masqué refuse tout démarrage : `is-enabled` le dit. Un service qui
échoue démarre sans erreur visible, et c'est `is-active` puis le journal qui
parlent. Lisez le journal **du service** avant de chercher ailleurs.

## 👥 Exercice 4 : un groupe pas encore pris en compte

Ouvrez une session, ajoutez le compte à un groupe, et comparez ce que voit la
session et ce que dit le système :

```bash
sudo groupadd essai-groupe && sudo useradd -m essai-compte && sudo usermod -aG adm essai-compte
sudo -u essai-compte sh -c 'sleep 2; echo "session ouverte avant : $(id -nG)"' &
sleep 1; sudo usermod -aG essai-groupe essai-compte
echo "systeme : $(id -nG essai-compte)"
wait
echo "session neuve : $(sudo -u essai-compte id -nG)"
sudo usermod -G essai-groupe essai-compte
echo "sans -a : $(id -nG essai-compte)"
```

```text
systeme : essai-compte adm essai-groupe
session ouverte avant : essai-compte adm
session neuve : essai-compte adm essai-groupe
sans -a : essai-compte essai-groupe
```

Une session garde les groupes de son ouverture. Le système, lui, est à jour :
il faut se reconnecter, pas recommencer. La dernière ligne montre le piège :
sans `-a`, `usermod -G` remplace la liste, et le compte a perdu `adm`.

## 📝 Exercice 5 : un fichier de configuration faux

Faites contrôler trois fichiers par le démon, sans le démarrer :

```bash
printf '{"log-driver": "json-file"}\n' > bon.json
printf '{"log-driver": "json-file",}\n' > virgule.json
printf '{"log-drivr": "json-file"}\n' > faute.json
for f in bon virgule faute; do echo "$f : $(sudo dockerd --validate --config-file $f.json 2>&1 | grep -oE 'configuration OK|invalid character.*|following directives.*' | head -1)"; done
```

```text
bon : configuration OK
virgule : invalid character '}' looking for beginning of object key string
faute : following directives don't match any configuration option: log-drivr
```

Une virgule de trop ou un nom inconnu empêche le démon de démarrer.
`--validate` le dit avant, sans toucher au service. C'est le contrôle à faire
avant toute relance.

## 🧹 Nettoyage

```bash
cd ~
sudo systemctl reset-failed essai-veille 2> /dev/null
sudo rm -f /etc/systemd/system/essai-veille.service && sudo systemctl daemon-reload
sudo userdel -r essai-compte 2> /dev/null; sudo groupdel essai-groupe
rm -rf ~/essai-moteur
getent passwd essai-compte | wc -l
```

```text
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset docker-verifier-son-moteur
dsoxlab check docker-verifier-son-moteur
```

```text
╭─ Résultat : docker-verifier-son-moteur ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests        │
╰─────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un moteur installé qui ne sert à rien, et quatre
preuves à apporter.

```bash
dsoxlab run docker-verifier-son-moteur
dsoxlab challenge docker-verifier-son-moteur
```
