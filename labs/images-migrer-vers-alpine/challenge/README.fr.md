# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux images et deux
socles sont déjà là :

```text
appli:lourde          elle MARCHE, et pèse 79 Mo
lab-socle-lourd:1.0   le socle Debian, 79 Mo
lab-socle-leger:1.0   le socle Alpine, 8 Mo
```

Le contexte est dans `/opt/lab-migration/appli`.

**Commencez par lancer `appli:lourde` et la peser.** Puis changez la ligne
`FROM` et construisez : lisez le message.

## 1. L'image légère doit rendre le bon résultat

`appli:legere` doit imprimer le même jeton, la même somme et le même maximum
que la référence.

Les données sont dans `donnees/valeurs.txt`, et leurs valeurs sont tirées à
chaque passage. Le contrôle recalcule le résultat lui-même : il ne compare pas
à un chiffre écrit quelque part.

Si le message nomme le script et dit qu'il est introuvable, **allez vérifier** :
il est là, exécutable. Ce qui manque est l'interpréteur de son shebang.

## 2. Elle doit être construite sur le socle léger

Le contrôle compare les **couches** : celles du socle léger doivent être le
préfixe des siennes.

Une image peut très bien marcher et peser le bon poids sans avoir changé de
socle. La mission est de migrer, et cela se lit dans les couches, pas dans un
fichier de version.

## 3. Elle doit peser une fraction de la référence

Le seuil est **dérivé** de `appli:lourde`, pesée au moment de la notation : son
tiers. Le socle léger pèse 8 Mo contre 79, la marge est donc très large.

Une image qui reste aussi lourde n'a pas changé de socle, ou emporte avec elle
ce que le socle fournit déjà.

## 4. Elle doit calculer, et non réciter

Le contrôle lui donne des données **qu'elle n'a jamais vues**, par un montage
sur `/donnees`, et attend le bon résultat.

Les trois premiers contrôles passeraient sur une application qui imprime un
résultat figé : les données du dépôt ne changent pas pendant une session. C'est
la raison d'être de celui-ci.

## Migrer, c'est adapter

Le script utilise deux constructions que son ancien socle lui donnait. Vous avez
deux voies, et les deux passent les contrôles :

- **réécrire** ce qui dépendait de l'ancien socle ;
- **installer** sur le nouveau ce qui manque.

La première est celle que ce lab défend : ajouter un interpréteur de 2 Mo pour
deux constructions dont l'une tient en une boucle revient à payer le socle qu'on
vient de quitter. Le choix reste le vôtre.

## Ce qui n'est pas noté

La commande que vous avez tapée, et le chemin choisi. Ne modifiez pas
`appli:lourde` : c'est la référence à laquelle vous êtes comparé.
