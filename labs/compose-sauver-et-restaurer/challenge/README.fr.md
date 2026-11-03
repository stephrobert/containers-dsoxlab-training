# Sauvegarder une stack Compose, et la restaurer ailleurs

La stack `herbier` tourne et sert. Vous devez la sauvegarder, la remonter dans
un projet **neuf** qui tourne à côté d'elle, et prouver que les données servies
sont les mêmes.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. La source tourne toujours, et sert comme avant

Ce contrôle ne mesure pas votre sauvegarde : il mesure qu'elle **n'a rien
coûté**.

Arrêter la base pour la copier tranquillement, la vider, déplacer son volume :
tout cela « marche » et laisse le conservatoire sans son herbier pendant
l'opération. C'est la faute la plus facile à commettre, parce qu'elle rend le
reste du travail plus simple.

Ses deux services doivent tourner, et son empreinte doit être **celle du
départ** : la source se lit, elle ne se modifie pas.

### 2. La sauvegarde de la base est logique, et se relit

Une copie du répertoire de données prise pendant que le moteur écrit **n'est pas
une sauvegarde**. Elle semble complète, elle porte un état intermédiaire, et
elle se restaure sans erreur jusqu'au jour où elle ne se restaure pas.

Le contrôle ne regarde pas **comment** l'archive a été faite, il regarde ce
qu'elle **est** : une sauvegarde logique se relit, et le contrôle la relit.

### 3. Les planches et la configuration sont archivées

Deux archives distinctes, et deux raisons distinctes.

Le volume de fichiers **ne vit pas dans la base** : aucun `pg_dump` ne
l'emporte. Et la configuration est ce qui permet de **reconstruire** la stack :
sans elle, vous détenez des données et rien pour les servir.

### 4. La cible est un projet distinct, et elle est debout

Restaurer par-dessus la source ne prouve rien : les données y étaient déjà.

La cible est donc un projet Compose à elle, et les deux **cohabitent**, ce qui
l'oblige à prendre son propre port publié. C'est aussi la situation réelle : on
vérifie une sauvegarde **avant** d'avoir perdu l'original.

### 5. La cible sert exactement les données de la source

**C'est le contrôle pour lequel ce lab existe.**

Deux empreintes, et chacune couvre ce que l'autre ne voit pas.

Celle de la base agrège le contenu **ordonné** de la table : compter les lignes
ne suffit pas, une table remplie de mauvaises valeurs a le bon compte. Celle des
planches est un `sha256sum` par fichier : un volume dont on recrée les fichiers à
la main a le bon nombre de fichiers, et pas les bons octets.

Deux valeurs sont tirées au sort à chaque passage, l'une dans la base et l'autre
dans une planche. Elles n'existent nulle part ailleurs que dans la source : on
ne peut ni les deviner ni les reconstituer.

### 6. La vitrine de la cible sert bien ses planches

Un volume juste et un service qui ne le monte pas donnent une cible qui
**détient** les planches sans les **servir**.

Le contrôle 5 lit le volume ; celui-ci lit ce qu'un visiteur obtient. Ce qui est
déclaré et ce qui est servi sont deux faits, et seul le second intéresse celui
qui vient consulter l'herbier.

## Le barème

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucun contrôle ne
regarde quelles commandes vous avez tapées : le chemin vous appartient.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
