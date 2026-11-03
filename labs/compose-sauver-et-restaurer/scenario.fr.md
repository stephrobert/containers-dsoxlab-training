# Sauvegarder un herbier, et le remettre en service ailleurs

Le conservatoire botanique range son herbier numérique dans une stack Compose :
une base PostgreSQL qui tient le catalogue des `specimens`, et une vitrine web
qui sert les planches scannées. Elle tourne, elle sert, et personne ne l'a
jamais sauvegardée.

Le bâtiment change de salle le mois prochain. On vous demande de **prouver**,
avant le déménagement, que cet herbier peut être remonté ailleurs à l'identique.

## L'état de départ

La stack `herbier` tourne dans `/opt/lab-sauver-restaurer/herbier` et sert ses
planches sur `http://127.0.0.1:18530/`. Sa configuration est complète :
`compose.yaml`, un `.env`, et le mot de passe de la base dans un fichier de
`secrets/`.

`/opt/lab-sauver-restaurer/sauvegardes` vous attend, vide, en 0700.

**Il n'y a rien à réparer.** La stack marche, et c'est ce qui rend l'exercice
difficile : il n'y a pas de panne à trouver, il y a une preuve à produire.

## Ce qui est demandé

1. **Sauvegarder** dans `/opt/lab-sauver-restaurer/sauvegardes` : la base, le
   volume des planches, et de quoi reconstruire la stack.

2. **Restaurer** dans un projet Compose **neuf**, nommé `herbier-reprise`, qui
   tourne **en même temps** que la source. Les deux ne peuvent pas publier le
   même port de l'hôte : la cible prendra le sien.

3. **Prouver** que la cible sert les mêmes données que la source : les mêmes
   lignes dans `specimens`, et les mêmes planches.

## Ce qui est interdit

Toucher à la source. Elle doit tourner et servir comme avant.

On ne casse pas ce qu'on est venu sauvegarder, et c'est la faute la plus
tentante : arrêter la base rend tout le reste plus simple.

## Le contrôle décisif

**Les données servies par la cible doivent égaler celles de la source.**

C'est le contrôle pour lequel ce lab existe. Une restauration qui rend des
données fausses est pire qu'une restauration qui échoue : un échec se voit et se
reprend, des données fausses se découvrent le jour où l'on en a besoin, et
l'herbier est perdu.

Le contrôle ne compte pas les lignes, il compare une **empreinte** du contenu :
une table remplie de mauvaises valeurs a le bon nombre de lignes.

## Comment c'est noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Le chemin vous
appartient : aucun contrôle ne regarde quelles commandes vous avez tapées.

Quatre indices sont disponibles, et **ils coûtent des points** :
`dsoxlab hint`.

L'énoncé complet est aussi sur la machine, dans
`/opt/lab-sauver-restaurer/MISSION.md`.
