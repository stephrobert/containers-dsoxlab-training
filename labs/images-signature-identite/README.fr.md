# Vérifier la signature d'une archive et l'identité de son signataire

La leçon signe une archive avec une autorité locale et vérifie en deux temps.
Ce cours montre les contrôles qui acceptent à tort : un certificat périmé, un
outil qui rend 0, une identité comparée trop vite, une clé sous deux noms, et
un fichier changé après le contrôle.

Vous travaillez dans `~/essai-signature`, avec votre propre autorité. Le
challenge porte sur `/opt/lab-image-signature` : n'utilisez ni ses clés ni ses
certificats pendant le cours.

Page associée : [Vérifier ce que contient une image, et qui l'a signée](https://www.stephane-robert.info/docs/conteneurisation/supply-chain-images/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-signature-identite
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `certifie` crée un
certificat signé par l'autorité : nom, identité, fichier de clé, durée en
jours. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-signature && cd ~/essai-signature
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 30 -subj /CN=essai-ca 2> /dev/null
certifie() {
  [ -e "$3" ] || openssl genrsa -out "$3" 2048 2> /dev/null
  openssl req -new -key "$3" -subj "/CN=$1" -out "$1.csr"
  printf 'subjectAltName=%s\n' "$2" > "$1.ext"
  openssl x509 -req -in "$1.csr" -CA ca.crt -CAkey ca.key -days "$4" -extfile "$1.ext" -out "$1.crt" 2> /dev/null
}
certifie equipe URI:spiffe://essai/equipe equipe.key 10
docker save "$IMAGE" -o archive.tar
openssl dgst -sha256 -sign equipe.key -out archive.sig archive.tar
openssl x509 -in equipe.crt -pubkey -noout > equipe.pub
openssl dgst -sha256 -verify equipe.pub -signature archive.sig archive.tar
```

```text
29.9.2
Verified OK
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## ⏳ Exercice 1 : un certificat périmé

Vérifiez un certificat d'un jour à la date d'aujourd'hui, puis à une date plus
lointaine :

```bash
certifie courte URI:spiffe://essai/equipe courte.key 1
openssl verify -CAfile ca.crt courte.crt
openssl verify -CAfile ca.crt -attime "$(date -d '+3 days' +%s)" courte.crt 2>&1 | grep -o 'certificate has expired'
openssl dgst -sha256 -sign courte.key -out courte.sig archive.tar
openssl x509 -in courte.crt -pubkey -noout > courte.pub
openssl dgst -sha256 -verify courte.pub -signature courte.sig archive.tar
```

```text
courte.crt: OK
certificate has expired
Verified OK
```

`dgst -verify` ne connaît que la clé : il dira toujours que la signature est
bonne, même périmée. La date se contrôle avec le certificat, par `openssl
verify`. `-attime` permet d'essayer une date, donc de prévoir.

## 🎭 Exercice 2 : un outil qui rend 0

Demandez l'identité d'un certificat qui n'en a pas, et lisez le code de sortie
:

```bash
openssl x509 -in ca.crt -noout -ext subjectAltName 2> /dev/null; echo "code: $?"
openssl x509 -in equipe.crt -noout -ext subjectAltName; echo "code: $?"
echo abime > faux.sig
openssl dgst -sha256 -verify equipe.pub -signature faux.sig archive.tar 2> /dev/null; echo "code: $?"
openssl verify -CAfile ca.crt absent.crt > /dev/null 2>&1; echo "code: $?"
```

```text
code: 0
X509v3 Subject Alternative Name:
    URI:spiffe://essai/equipe
code: 0
Verification failure
code: 1
code: 2
```

Le certificat sans identité rend 0, comme l'autre : seul le texte diffère, et
il n'est pas sur la sortie attendue. Un programme qui ne lit que le code
accepterait une identité vide. Exigez une valeur, puis comparez-la.

## 🔍 Exercice 3 : une identité comparée trop vite

Créez une identité qui commence comme la bonne, une seconde qui en cache une
autre, et cherchez la bonne :

```bash
certifie voisine URI:spiffe://essai/equipe-invitee voisine.key 10
certifie double URI:spiffe://essai/autre,URI:spiffe://essai/equipe double.key 10
for c in equipe voisine double; do
  openssl x509 -in $c.crt -noout -ext subjectAltName | grep -q 'spiffe://essai/equipe' && echo "$c : trouve par grep"
  echo "   identites : $(openssl x509 -in $c.crt -noout -ext subjectAltName | tail -n +2 | tr -d ' ')"
done
```

```text
equipe : trouve par grep
   identites : URI:spiffe://essai/equipe
voisine : trouve par grep
   identites : URI:spiffe://essai/equipe-invitee
double : trouve par grep
   identites : URI:spiffe://essai/autre,URI:spiffe://essai/equipe
```

La recherche de texte accepte les trois. La première erreur vient d'un début
commun, la seconde d'un certificat qui porte plusieurs identités. Décidez de la
règle avant d'écrire le contrôle : ici, une seule identité, et égale.

## 👯 Exercice 4 : une clé sous deux noms

Faites certifier la même clé sous une autre identité, et vérifiez la signature
avec les deux certificats :

```bash
certifie invite URI:spiffe://essai/invite equipe.key 10
openssl x509 -in invite.crt -pubkey -noout > invite.pub
openssl dgst -sha256 -verify invite.pub -signature archive.sig archive.tar
cmp equipe.pub invite.pub && echo 'meme cle'
for c in equipe invite; do openssl x509 -in $c.crt -noout -fingerprint -sha256 | cut -c1-40; done | sort -u | wc -l
```

```text
Verified OK
meme cle
2
```

La signature est bonne avec les deux : elle lie une clé, pas un nom. C'est le
certificat présenté qui donne le nom. Il faut donc le contrôler à chaque fois,
et ne jamais l'extraire d'un fichier fourni par l'auteur sans le rattacher à
l'autorité.

## ⏱️ Exercice 5 : un fichier changé après le contrôle

Vérifiez l'archive, changez-la, et chargez-la quand même ; puis ajoutez-lui
seulement un octet :

```bash
cp archive.tar recue.tar
controle() { openssl dgst -sha256 -verify equipe.pub -signature archive.sig "$1" 2> /dev/null; }
controle recue.tar && docker pull -q busybox:1.36.1 > /dev/null && docker save busybox:1.36.1 -o recue.tar && docker load -q -i recue.tar
cp archive.tar recue.tar && printf x >> recue.tar
docker load -q -i recue.tar | cut -c1-40
controle recue.tar
docker rmi busybox:1.36.1 > /dev/null
```

```text
Verified OK
Loaded image: busybox:1.36.1
Loaded image ID: sha256:be2656061b536c18
Verification failure
```

Le premier chargement n'a plus rien à voir avec ce qui a été vérifié. Copiez
d'abord l'archive là où personne d'autre n'écrit, puis contrôlez et chargez
cette copie. L'octet ajouté ne gêne pas `docker load`, mais la signature le
voit.

## 🧹 Nettoyage

```bash
cd ~
rm -rf ~/essai-signature
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
dsoxlab reset images-signature-identite
dsoxlab check images-signature-identite
```

```text
╭─ Résultat : images-signature-identite ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests       │
╰────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une porte à écrire, qui n'ouvre qu'au bon signataire.

```bash
dsoxlab run images-signature-identite
dsoxlab challenge images-signature-identite
```
