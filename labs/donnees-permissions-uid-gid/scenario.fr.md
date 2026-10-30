# « Mets-le en root, ça marchera »

## La situation

Un service produit des rapports dans un volume. Le jour de sa mise en service,
il n'arrivait pas à écrire : le volume appartenait à root et le conteneur
tournait sous un compte ordinaire. La console affichait `Permission denied`, la
mise en production attendait, et quelqu'un a dit la phrase qu'on entend
toujours : « mets-le en root, ça marchera ».

Ça a marché. Le service écrit, et chaque rapport qu'il produit appartient à
root.

Six mois plus tard, on ajoute un second conteneur, un relecteur qui doit
reprendre ces rapports. Lui, on l'a fait correctement : il tourne sous un compte
ordinaire. Et il n'écrit rien.

La prochaine phrase qui vient est « mets le volume en 777 ». Elle marcherait
aussi.

## L'objectif

Remplacer les deux mauvaises réponses par celle qui tient. Deux conteneurs
partagent le volume `rapports-partages`, monté sur `/rapports`, et l'image porte
deux comptes dans le **même groupe** :

```text
redacteur       uid 1000, groupe equipe (gid 2000)
verificateur    uid 1001, groupe equipe (gid 2000)
```

L'état actuel est le résultat de l'histoire ci-dessus :

```text
rapport        tourne en ROOT, parce que sinon il n'écrivait pas
verificateur   tourne en non-root, et il n'écrit rien
```

Quatre choses sont attendues :

1. `rapport` **ne tourne plus en root**.
2. Un fichier que `rapport` écrit dans `/rapports` lui appartient, et porte le
   **groupe partagé**.
3. Le répertoire `/rapports` appartient au groupe partagé et lui donne
   l'**écriture**.
4. `verificateur`, dont l'uid est **différent**, écrit aussi dans `/rapports`,
   et le répertoire n'est **pas** ouvert en écriture à tout le monde.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Pourquoi le groupe, et pas le propriétaire

Deux conteneurs doivent écrire sous **deux uid différents**. Aucun propriétaire
ne peut convenir aux deux : donner le volume à `1000` ferait écrire le
producteur et pas le relecteur.

Un groupe partagé, lui, convient aux deux. C'est la situation réelle dès qu'une
application et son outil de sauvegarde se partagent des données, et c'est pour
cela que ce lab porte deux conteneurs plutôt qu'un.

## Deux choses à savoir avant de commencer

**L'utilisateur d'un conteneur se fixe à sa création** : il faut le recréer.
C'est la même règle que pour les montages, les ports publiés et le réseau.

Et **on ne peut pas écrire dans un volume sans un conteneur qui le monte**. Pour
changer ses droits, lancez-en un jetable qui le monte, avec les privilèges qu'il
faut.

## Ce qui est noté

L'**état du système**, et il est mesuré par l'**écriture réelle**, pas seulement
par la lecture des permissions. Une permission se déclare sans toujours produire
l'effet attendu, et c'est l'effet qui compte.

Le quatrième contrôle refuse explicitement un volume ouvert en écriture à tout
le monde. `chmod 777` ferait passer les trois premiers : il marche, et il donne
à n'importe quel processus du conteneur le droit de tout réécrire. Le groupe
partagé suffit, et il **nomme** qui peut écrire.
