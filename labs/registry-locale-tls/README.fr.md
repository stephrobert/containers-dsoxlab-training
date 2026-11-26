# Servir un registre de confiance et tirer sans désactiver TLS

La leçon crée une autorité, sert un registre en TLS et l'accepte côté Docker.
Ce cours provoque les refus un par un : une adresse qui n'est pas la boucle
locale, un certificat sans nom, une clé qui n'est pas la bonne, un fichier mal
rangé, et une date qui approche.

Vous travaillez dans `~/essai-tls`, sur le registre `essai-reg` et le port
15950. Le challenge porte sur `registry-tls.lab.test` et le port 15443 : n'y
touchez pas pendant le cours.

Page associée : [Servir un registre de confiance, et s'y authentifier](https://www.stephane-robert.info/docs/conteneurs/registres/distribution/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run registry-locale-tls
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `HOTE` est l'adresse de
la machine sur son réseau. `certifie` signe un certificat, `sert` lance le
registre avec lui. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-tls && cd ~/essai-tls
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
export REG=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
HOTE=$(ip -4 route get 1.1.1.1 | awk '{for(i=1;i<NF;i++) if($i=="src") print $(i+1)}')
openssl req -x509 -newkey rsa:2048 -nodes -days 2 -keyout ac.key -out ac.crt -subj /CN=ac-essai 2> /dev/null
certifie() { openssl req -newkey rsa:2048 -nodes -keyout $1.key -out $1.csr -subj "/CN=$HOTE" 2> /dev/null; echo "$2" > $1.ext; openssl x509 -req -in $1.csr -CA ac.crt -CAkey ac.key -CAcreateserial -out $1.crt -extfile $1.ext -days 2 2> /dev/null; chmod 644 $1.key; }
sert() { docker rm -f -v essai-reg > /dev/null 2>&1; docker run -d --name essai-reg -p 15950:5000 -v "$PWD:/c:ro" -e REGISTRY_HTTP_TLS_CERTIFICATE=/c/$1 -e REGISTRY_HTTP_TLS_KEY=/c/$2 "$REG" > /dev/null; sleep 2; }
tire() { docker pull -q "$HOTE:15950/essai:1" 2>&1 | grep -oE 'x509.*|failed to load.*|server gave HTTP.*|: not found'; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔁 Exercice 1 : la boucle locale fait exception

Servez un registre sans TLS, puis joignez-le par deux adresses :

```bash
docker run -d --name essai-reg -p 15950:5000 "$REG" > /dev/null; sleep 2
docker tag "$IMAGE" 127.0.0.1:15950/essai:1
docker push -q 127.0.0.1:15950/essai:1 2> /dev/null | head -1
tire
docker rmi 127.0.0.1:15950/essai:1 > /dev/null
```

```text
127.0.0.1:15950/essai:1
server gave HTTP response to HTTPS client
```

Docker accepte le HTTP simple sur la boucle locale et nulle part ailleurs. Un
essai réussi sur `127.0.0.1` ne dit donc rien de ce qui se passera depuis une
autre machine.

## 🪪 Exercice 2 : un certificat sans le bon nom

Faites confiance à l'autorité, puis servez trois certificats signés par elle :

```bash
DOSSIER="/etc/docker/certs.d/$HOTE:15950"
sudo mkdir -p "$DOSSIER" && sudo cp ac.crt "$DOSSIER/"
certifie sans ''
certifie autre 'subjectAltName=DNS:autre.test'
certifie bon "subjectAltName=IP:$HOTE"
for c in sans autre bon; do sert $c.crt $c.key; echo "$c $(tire | sed "s/$HOTE/ADRESSE/")"; done
```

```text
sans x509: certificate relies on legacy Common Name field, use SANs instead
autre x509: cannot validate certificate for ADRESSE because it doesn't contain any IP SANs
bon : not found
```

L'autorité est connue dans les trois cas. Docker exige que le nom ou l'adresse
soit dans `subjectAltName` : le champ `CN`, même juste, ne compte pas. Le
dernier message, `not found`, est une bonne nouvelle : la connexion est
établie, et l'image n'existe pas.

## 🔑 Exercice 3 : une clé qui n'est pas la bonne

Servez le bon certificat avec la clé d'un autre :

```bash
sert bon.crt autre.key
docker ps -a --filter name=essai-reg --format '{{.Status}}' | cut -d' ' -f1,2
docker logs essai-reg 2>&1 | grep -o 'tls: private key[^"]*' | head -1
[ "$(openssl x509 -in bon.crt -noout -pubkey | sha256sum)" = "$(openssl pkey -in bon.key -pubout | sha256sum)" ] && echo 'bon.key : la paire correspond'
```

```text
Exited (1)
tls: private key does not match public key
bon.key : la paire correspond
```

Le registre refuse de démarrer, et son journal dit pourquoi. Un certificat et
sa clé portent la même clé publique : comparez leurs empreintes avant de
redémarrer un service.

## 🗂️ Exercice 4 : un fichier mal rangé

Déplacez l'autorité dans le dossier de confiance, et tirez à chaque fois :

```bash
sert bon.crt bon.key
sudo mv "$DOSSIER/ac.crt" "$DOSSIER/ac.pem"; tire
sudo mv "$DOSSIER/ac.pem" "$DOSSIER/ac.cert"; tire
sudo mkdir "/etc/docker/certs.d/$HOTE" && sudo mv "$DOSSIER/ac.cert" "/etc/docker/certs.d/$HOTE/ac.crt"; tire
sudo mv "/etc/docker/certs.d/$HOTE/ac.crt" "$DOSSIER/"; tire
curl -sS --noproxy '*' "http://$HOTE:15950/v2/"; echo "code: $?"
```

```text
x509: certificate signed by unknown authority
failed to load X509 key pair: tls: found a certificate rather than a key in the PEM for the private key
x509: certificate signed by unknown authority
: not found
Client sent an HTTP request to an HTTPS server.
code: 0
```

L'extension `.crt` désigne une autorité, `.cert` un certificat client qui
attend sa clé, et `.pem` est ignoré. Le port fait partie du nom du dossier.
Aucun redémarrage n'est nécessaire : Docker relit ce dossier à chaque
connexion. Notez que `curl` en HTTP rend 0 sur un service TLS : c'est le texte
qu'il faut lire.

## 📅 Exercice 5 : une date qui approche

Demandez si le certificat sera encore valable dans une heure, puis dans un mois
:

```bash
openssl x509 -in bon.crt -checkend 3600; echo "code: $?"
openssl x509 -in bon.crt -checkend 2592000; echo "code: $?"
openssl s_client -connect "$HOTE:15950" -CAfile ac.crt < /dev/null 2> /dev/null | openssl x509 -noout -checkend 3600
```

```text
Certificate will not expire
code: 0
Certificate will expire
code: 1
Certificate will not expire
```

`-checkend` rend 1 quand la date sera passée dans le délai donné : il se met
tel quel dans une surveillance. La dernière forme interroge le service en
marche, et non le fichier : c'est elle qui voit un certificat renouvelé mais
pas encore servi.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f -v essai-reg > /dev/null
sudo rm -r "/etc/docker/certs.d/$HOTE:15950" "/etc/docker/certs.d/$HOTE"
rm -rf ~/essai-tls
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
dsoxlab reset registry-locale-tls
dsoxlab check registry-locale-tls
```

```text
╭─ Résultat : registry-locale-tls ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un registre qui répond, et un moteur qui a raison de
se méfier.

```bash
dsoxlab run registry-locale-tls
dsoxlab challenge registry-locale-tls
```
