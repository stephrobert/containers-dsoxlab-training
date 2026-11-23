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

## Sauvegarder une stack Compose, et la restaurer ailleurs

La stack `herbier` tourne et sert. Vous devez la sauvegarder, la remonter dans
un projet **neuf** qui tourne à côté d'elle, et prouver que les données servies
sont les mêmes.

### Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

#### 1. La sauvegarde de la base est logique, et se relit

Une copie du répertoire de données prise pendant que le moteur écrit **n'est pas
une sauvegarde**. Elle semble complète, elle porte un état intermédiaire, et
elle se restaure sans erreur jusqu'au jour où elle ne se restaure pas.

Le contrôle ne regarde pas **comment** l'archive a été faite, il regarde ce
qu'elle **est** : une sauvegarde logique se relit, et le contrôle la relit.

#### 2. Les planches et la configuration sont archivées

Deux archives distinctes, et deux raisons distinctes.

Le volume de fichiers **ne vit pas dans la base** : aucun `pg_dump` ne
l'emporte. Et la configuration est ce qui permet de **reconstruire** la stack :
sans elle, vous détenez des données et rien pour les servir.

#### 3. La cible est un projet distinct, et elle est debout

Restaurer par-dessus la source ne prouve rien : les données y étaient déjà.

La cible est donc un projet Compose à elle, et les deux **cohabitent**, ce qui
l'oblige à prendre son propre port publié. C'est aussi la situation réelle : on
vérifie une sauvegarde **avant** d'avoir perdu l'original.

#### 4. La cible sert exactement les données de la source

**C'est le contrôle pour lequel ce lab existe.**

**Et il exige que la source soit intacte.** Ce n'est pas un contrôle à part,
c'est une condition de celui-ci : comparer l'empreinte de la cible à celle de la
source n'a de sens que si la source est encore celle du départ. Une restauration
prouvée contre une source détruite ne prouve rien.

Arrêter la base pour la copier tranquillement, la vider, déplacer son volume :
tout cela « marche » et laisse le conservatoire sans son herbier pendant
l'opération. C'est la faute la plus facile à commettre, parce qu'elle rend le
reste du travail plus simple, et elle coûte ce contrôle-ci.

Deux empreintes, et chacune couvre ce que l'autre ne voit pas.

Celle de la base agrège le contenu **ordonné** de la table : compter les lignes
ne suffit pas, une table remplie de mauvaises valeurs a le bon compte. Celle des
planches est un `sha256sum` par fichier : un volume dont on recrée les fichiers à
la main a le bon nombre de fichiers, et pas les bons octets.

Deux valeurs sont tirées au sort à chaque passage, l'une dans la base et l'autre
dans une planche. Elles n'existent nulle part ailleurs que dans la source : on
ne peut ni les deviner ni les reconstituer.

#### 5. La vitrine de la cible sert bien ses planches

Un volume juste et un service qui ne le monte pas donnent une cible qui
**détient** les planches sans les **servir**.

Le contrôle 4 lit le volume ; celui-ci lit ce qu'un visiteur obtient. Ce qui est
déclaré et ce qui est servi sont deux faits, et seul le second intéresse celui
qui vient consulter l'herbier.

### Le barème

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucun contrôle ne
regarde quelles commandes vous avez tapées : le chemin vous appartient.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
