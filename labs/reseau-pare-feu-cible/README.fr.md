# Réparer un flux routé sans retirer les protections

La leçon sonde un flux à plusieurs sauts et pose des règles sur l'hôte. Ce
cours monte un petit routeur à part, et montre ce qui trompe un diagnostic : un
retour oublié, une règle placée trop loin, deux refus qui ne se ressemblent
pas, une connexion déjà établie, et un fichier de règles à moitié faux.

Vous travaillez dans trois espaces réseau `essai-c`, `essai-r` et `essai-s` :
un client, un routeur, un serveur. Le pare-feu de la machine n'est pas touché.
Le challenge porte sur les conteneurs de son projet : n'y touchez pas pendant
le cours.

Page associée : [Diagnostiquer réseau et pare-feu](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/reseau-et-pare-feu/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run reseau-pare-feu-cible
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `C`, `R` et `S` lancent
une commande dans chaque espace, `va` demande une page depuis le client, `vide`
efface les règles du routeur. **Gardez le même terminal jusqu'au nettoyage** :
les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-routes && cd ~/essai-routes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
for n in c r s; do sudo ip netns add essai-$n; done
C() { sudo ip netns exec essai-c "$@"; }; R() { sudo ip netns exec essai-r "$@"; }; S() { sudo ip netns exec essai-s "$@"; }
sudo ip link add ec type veth peer name erc && sudo ip link set ec netns essai-c && sudo ip link set erc netns essai-r
sudo ip link add es type veth peer name ers && sudo ip link set es netns essai-s && sudo ip link set ers netns essai-r
C ip addr add 10.77.1.10/24 dev ec; R ip addr add 10.77.1.1/24 dev erc
S ip addr add 10.77.2.10/24 dev es; R ip addr add 10.77.2.1/24 dev ers
C ip link set ec up; R ip link set erc up; S ip link set es up; R ip link set ers up
R sysctl -qw net.ipv4.ip_forward=1
C ip route add default via 10.77.1.1
mkdir page && echo bonjour > page/index.html
S python3 -m http.server 8080 --directory page > /dev/null 2>&1 &
sleep 1
va() { C curl -s -m 2 "http://10.77.2.10:${1:-8080}/"; echo "code: $?"; }
vide() { R iptables -F FORWARD; R iptables -P FORWARD ACCEPT; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## ↩️ Exercice 1 : un retour oublié

Demandez la page, regardez où va la demande, puis donnez au serveur une route
de retour :

```bash
va
C ip route get 10.77.2.10 | head -1 | grep -o 'via [0-9.]*'
S ip route get 10.77.1.10 2>&1
R iptables -A FORWARD -d 10.77.2.10 && va
R iptables -vnL FORWARD | awk 'NR==3{print ($1 > 0 ? "la demande est passee" : "rien n est passe")}'
vide
S ip route add 10.77.1.0/24 via 10.77.2.1
va
```

```text
code: 28
via 10.77.1.1
RTNETLINK answers: Network is unreachable
code: 28
la demande est passee
bonjour
code: 0
```

Le routeur a bien transmis la demande : c'est le serveur qui ne savait pas où
répondre. Une règle sans action ne fait que compter, ce qui en fait une sonde
sans effet. Vérifiez les deux sens avant d'accuser un pare-feu.

## 🔢 Exercice 2 : une règle placée trop loin

Refusez tout, puis ajoutez l'autorisation à la fin, et lisez les compteurs :

```bash
R iptables -A FORWARD -j DROP
R iptables -A FORWARD -p tcp --dport 8080 -j ACCEPT
va
R iptables -vnL FORWARD | awk 'NR>2{print $3, ($1 > 0 ? "a servi" : "n a jamais servi")}'
R iptables -D FORWARD 2 && R iptables -I FORWARD 1 -p tcp --dport 8080 -j ACCEPT
va
R iptables -I FORWARD 2 -p tcp --sport 8080 -j ACCEPT
va
vide
```

```text
code: 28
DROP a servi
ACCEPT n a jamais servi
code: 28
bonjour
code: 0
```

Les règles se lisent dans l'ordre, et la première qui décide l'emporte. Une
autorisation au compteur nul est une règle que rien n'atteint. Placée devant,
elle laisse passer l'aller ; il faut encore laisser passer la réponse.

## 🚧 Exercice 3 : deux refus qui ne se ressemblent pas

Refusez de deux façons, puis visez un port où rien n'écoute, et comparez les
codes de `curl` :

```bash
R iptables -A FORWARD -p tcp --dport 8080 -j DROP; echo 'DROP'; va; vide
R iptables -A FORWARD -p tcp --dport 8080 -j REJECT --reject-with tcp-reset; echo 'REJECT'; va; vide
echo 'port ferme'; va 8099
S ss -ltnH 'sport = :8080' | awk '{print $4}'
```

```text
DROP
code: 28
REJECT
code: 7
port ferme
code: 7
*:8080
```

`DROP` fait attendre, code 28. `REJECT` répond tout de suite, code 7,
exactement comme un port fermé. Un « connexion refusée » ne prouve donc pas que
le service est arrêté : regardez ce qui écoute sur le serveur.

## 🔗 Exercice 4 : une connexion déjà établie

Ouvrez une connexion longue, puis interdisez les nouvelles :

```bash
R iptables -P FORWARD DROP
R iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
R iptables -A FORWARD -p tcp --dport 8080 -m conntrack --ctstate NEW -j ACCEPT
va
cat > longue.py <<'EOF'
import socket, time
s = socket.create_connection(("10.77.2.10", 8080), 2)
time.sleep(3)
s.sendall(b"GET / HTTP/1.0\r\n\r\n")
d = b""
while (m := s.recv(999)):
    d += m
print("ancienne connexion :", d.split(b"\r\n\r\n")[1].decode().strip())
EOF
C python3 longue.py & P=$!
sleep 1; R iptables -D FORWARD 2; va; wait $P
```

```text
bonjour
code: 0
ancienne connexion : bonjour
code: 28
```

Les nouvelles demandes sont refusées, et l'ancienne connexion reçoit encore sa
réponse : la règle des connexions établies la laisse passer. Après un
changement de règle, testez avec une connexion neuve, et n'oubliez pas celles
qui durent.

## 📄 Exercice 5 : un fichier de règles à moitié faux

Chargez un fichier dont la dernière ligne est fausse, puis un fichier juste qui
perd la politique :

```bash
R iptables-save -t filter > bon.txt
{ grep -v COMMIT bon.txt; echo '-A FORWARD -p tcp --dport 8080 -j ACCEPTE'; echo COMMIT; } > faux.txt
R iptables-restore < faux.txt 2> /dev/null; echo "code: $?"
R iptables-save -t filter | grep -v '^#' | sed 's/\[.*//' | cmp -s - <(grep -v '^#' bon.txt | sed 's/\[.*//') && echo 'regles inchangees'
vide; R iptables -S FORWARD
R iptables-restore < bon.txt && R iptables -S FORWARD
```

```text
code: 2
regles inchangees
-P FORWARD ACCEPT
-P FORWARD DROP
-A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

Le fichier se charge en entier ou pas du tout : une ligne fausse laisse les
règles d'avant. C'est plus sûr qu'une suite de commandes, qui s'arrête au
milieu. Effacer les règles, en revanche, ouvre tout si la politique revient à
`ACCEPT` : gardez une sauvegarde avant d'essayer.

## 🧹 Nettoyage

```bash
cd ~
sudo pkill -f '^python3 -m http.server 8080 --directory page'
for n in c r s; do sudo ip netns del essai-$n; done
ip netns list | grep -c essai
rm -rf ~/essai-routes
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
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
dsoxlab reset reseau-pare-feu-cible
dsoxlab check reseau-pare-feu-cible
```

```text
╭─ Résultat : reseau-pare-feu-cible ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests   │
╰────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un flux à rétablir, et toutes les autres portes à
garder fermées.

```bash
dsoxlab run reseau-pare-feu-cible
dsoxlab challenge reseau-pare-feu-cible
```
