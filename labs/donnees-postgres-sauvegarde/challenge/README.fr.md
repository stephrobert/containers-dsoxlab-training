# Ce qui est demandé

Sur `docker.lab`, une base PostgreSQL source porte trois lignes de commandes.
Sur `docker-client.lab`, une seconde VM, rien n'existe encore. Les noms uniques
des bases, le marqueur de propriété et le répertoire de sauvegarde sont dans
`/opt/lab-postgres-sauvegarde/state.env` ; les lignes attendues sont dans
`state.json`.

```text
SOURCE_DB     la base à sauvegarder, sur docker.lab
RESTORED_DB   la base à créer, sur docker-client.lab
BACKUP_DIR    le répertoire de sauvegarde, inscriptible
OWNERSHIP     le marqueur exact à poser sur la base restaurée
```

Les noms sont tirés au hasard à chaque session, pour que le nettoyage ne touche
jamais une base préexistante au nom courant.

## 1. La sauvegarde existe, au format personnalisé

`BACKUP_DIR/orders.dump` doit exister et commencer par `PGDMP`.

Le contrôle lit la **signature**, pas l'extension : une sauvegarde SQL en clair
porterait le même nom de fichier sans être au même format. C'est `pg_dump -Fc`
qui produit le format personnalisé, le seul que `pg_restore` sait rejouer
sélectivement.

## 2. La sauvegarde a été transférée à l'identique

Le fichier doit exister **au même chemin** sur `docker-client.lab`, avec la
**même empreinte SHA-256** que celui de `docker.lab`.

C'est l'anti-triche de ce défi, et il vaut d'être compris. Sans cette mesure,
recréer les trois lignes à la main sur la seconde VM passerait tous les autres
contrôles : les lignes y seraient, la base aussi, le marqueur aussi. L'empreinte
exige que le fichier qui a servi soit **celui qui a été produit**, et c'est la
seule mesure qui distingue une restauration d'une recopie.

## 3. Le service cible répond, et la base porte son marqueur

Deux choses, dans cet ordre : PostgreSQL doit répondre à une requête réelle sur
`docker-client.lab`, puis `RESTORED_DB` doit y exister avec le commentaire
`OWNERSHIP` **exact**.

L'ordre compte. Si le service est muet, toute question sur une base rend la même
erreur, et un contrôle qui ne les distinguerait pas vous enverrait créer une
base alors que c'est le moteur qu'il faut démarrer.

## 4. La base restaurée porte toutes les lignes, et la source n'a pas bougé

Les lignes de `RESTORED_DB` sont comparées à l'ensemble attendu, **ordonné** et
non compté : trois lignes dont une valeur a changé donnent le même compte que
trois lignes justes.

Et la source est vérifiée ici même : ses lignes **et** son marqueur. Restaurer
sur `docker.lab` au lieu de la seconde VM ne satisfait pas ce défi, et un
`dropdb` suivi d'un `createdb` effacerait le commentaire sans toucher aux
lignes.

## 5. La sauvegarde se restaure dans une base vierge

Le contrôle crée une base jetable sur `docker-client.lab`, y rejoue votre
sauvegarde, compare les lignes, puis la supprime.

C'est la différence entre « ça marche aujourd'hui » et « la sauvegarde est
bonne ». Les contrôles précédents constatent un état ; celui-ci répond à la
seule question qui compte le jour où l'on s'en sert : ce fichier reproduit-il la
base, ailleurs, à partir de rien ?

## Ce qui n'est pas noté, et pourquoi on vous le dit

Avant de rejouer votre sauvegarde, le contrôle 5 vérifie que `pg_restore`
**refuse** un fichier invalide. Ce n'est pas une exigence pour vous : vous ne
pouvez ni la provoquer ni la rater. C'est la condition pour que le succès
annoncé ensuite veuille dire quelque chose, car un outil qui annoncerait un
succès sur un fichier vide ne prouverait rien sur le vôtre. Si ce garde-fou
échoue, le message vous dit que ce n'est pas votre faute.
