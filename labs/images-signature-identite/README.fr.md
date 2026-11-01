# Signature et identité approuvée

**Langue :** [English](README.md) · [Français](README.fr.md)

## Octets, clés et identité

Un digest SHA-256 identifie des octets. Une signature lie les octets à une clé
privée. Un certificat vérifié lie sa clé publique à une identité sous un
émetteur de confiance. La politique de livraison doit contrôler les trois ;
une signature valide de la mauvaise équipe reste inacceptable.

Pour un exemple neutre jetable, créez un message et une clé synthétique :

```sh
printf 'workshop message\n' > note.txt
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out workshop.key
openssl pkey -in workshop.key -pubout -out workshop.pub
openssl dgst -sha256 -sign workshop.key -out note.sig note.txt
openssl dgst -sha256 -verify workshop.pub -signature note.sig note.txt
```

Ces commandes démontrent seulement la vérification des octets. Elles
n'établissent pas quelle identité possède `workshop.pub`. Dans une porte
fondée sur les certificats, utilisez d'abord `openssl verify` avec une CA
approuvée administrativement. Lisez le SAN URI exact approuvé seulement dans
ce certificat validé, extrayez sa clé publique, puis vérifiez la signature
détachée des octets livrés. Ne faites jamais confiance à un sujet textuel ou
à un certificat fourni par son propre signataire sans valider la chaîne.
Refusez les entrées malformées et les erreurs des outils.

## Modèle de confiance local

Ce lab implémente des signatures détachées RSA/SHA-256 avec OpenSSL et une CA
X.509 locale. Ce n'est ni Sigstore, ni OIDC sans clé, ni un journal de
transparence, ni une autorité d'identité en ligne. Les clés privées et les
certificats de courte durée sont générés seulement dans la VM.
`trust/ca.crt` et `trust/policy.json` sont des entrées de confiance de
l'administrateur, pas des données fournies par l'éditeur de l'archive.
L'exercice suppose l'administrateur local digne de confiance ; il ne protège
pas contre root remplaçant le vérificateur ou émettant de nouveaux
certificats avec la clé de CA.

`archive.tar` est un véritable Docker save d'une image neuve construite
depuis une base publique épinglée par digest. La signature couvre les octets
de l'archive, pas un tag de registre, un enregistrement Docker content trust
ni une signature OCI publiée à distance. Réexporter la même image peut
changer les octets et nécessite une nouvelle signature. Ce lab authentifie
la provenance et l'intégrité ; il ne mesure pas les vulnérabilités.
Le scan relève du lab CVE distinct.

## Contre-exemples

Les contrôles utilisent des octets aléatoires neufs et de véritables
signatures, pas une sortie console attendue. L'identité approuvée doit
réussir. Une seconde identité signée par la même CA doit échouer, comme
un certificat auto-émis revendiquant l'URI approuvé, une signature faite
par une autre clé et des octets altérés.

[Mission](scenario.fr.md) · [Exigences](challenge/README.fr.md)
