# Ce qui est demandé

Deux machines. `docker.lab` construit et publie : elle porte le contexte de
construction, le secret, et le compte de publication. `docker-client.lab` est un
client **nu** : il a la confiance de l'autorité du lab et un compte **en lecture
seule**, rien d'autre.

Un registre privé en TLS vérifié écoute sur `livraison.lab.test:15401`, dépôt
`livraison/appli`. Les identifiants sont dans
`/opt/lab-livraison/identifiants-publication.json` sur l'hôte de publication, et
dans `/opt/lab-livraison/identifiants-lecture.json` sur le client.

C'est une **épreuve** : le seuil de réussite est de 75 %.

## 1. Construire l'image sans que le secret survive

Le contexte est dans `/opt/lab-livraison/build`. Le `Dockerfile` est à compléter.

L'image doit porter `/app/empreinte.txt` contenant l'**empreinte SHA-256 du
fichier** `/opt/lab-livraison/build/jeton-de-build.txt`, octet pour octet. C'est
ce que rend `sha256sum` sur ce fichier.

Le secret lui-même ne doit survivre dans **aucune couche**. Un secret monté le
temps d'une instruction n'y entre pas ; un secret copié, passé en argument de
construction ou posé en variable d'environnement y entre, et se relit dans
l'historique de l'image.

## 2. Publier dans le registre, avec le compte qui en a le droit

Poussez l'image sous `livraison.lab.test:15401/livraison/appli:1.0`.

Consignez ensuite dans `/opt/lab-livraison/livraison.txt`, une ligne par entrée,
sans espace autour du signe égal :

```text
reference_par_digest=<livraison.lab.test:15401/livraison/appli@sha256:...>
empreinte_du_secret=<l'empreinte SHA-256 du fichier de secret>
```

La référence est celle que le registre sert, **par digest** : c'est la seule qui
désigne une image et non une étiquette déplaçable.

## 3. La faire tourner sur le client nu, par ce digest

Sur `docker-client.lab`, tirez l'image **par le digest de la livraison** avec le
compte en lecture seule, et faites-la tourner sous le nom
`dsoxlab-livraison-client`.

Elle doit répondre l'empreinte sur son port 8080. C'est ce qui prouve qu'elle est
réellement utilisable ailleurs, et pas seulement sur la machine qui l'a
construite.

## 4. Établir que le client ne peut pas publier

Un compte en lecture seule ne doit pas pouvoir pousser. Vérifiez-le, et sachez
le vérifier : repousser une image que le registre possède déjà ne prouve rien,
le client n'écrit alors rien du tout.

Ce contrôle est mesuré sur la machine, vous n'avez rien à consigner pour lui.

## L'état final attendu

L'image est publiée, la livraison est remplie, le conteneur tourne sur le client
nu et répond l'empreinte, et le secret ne se trouve dans aucune couche.

## Ce qui n'est pas noté

Le nombre d'étapes de votre construction, la façon dont vous montez le secret,
ni les commandes que vous avez tapées. Le contrôle lit l'image produite et
l'état des deux machines.
