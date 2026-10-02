# Une API qui ne sait pas voyager

## La situation

Votre équipe livre une petite API d'inventaire, deux routes en FastAPI, que
les autres équipes commencent à vouloir. Elle tourne parfaitement sur le poste
de celle qui l'a écrite, et nulle part ailleurs.

Le dernier déploiement l'a montré. Le serveur de recette n'avait pas la bonne
version de Python, puis il manquait `uvicorn`, puis le `pip install` est passé
par un dépôt interne qui ne connaissait pas FastAPI. Trois heures, et l'API
répondait enfin.

Le répertoire `challenge/work` contient l'application telle qu'elle est livrée
aujourd'hui : `app/main.py`, et `app/requirements.txt` qui nomme ses deux
dépendances. Il n'y a aucun Dockerfile.

## L'objectif

Faire voyager cette application : une image qui l'embarque, avec son
interpréteur et ses dépendances, de sorte qu'elle réponde là où on la pose.

Elle doit partir de `debian:12`, parce que toute la série repart de cette image
pour montrer, mesure après mesure, ce que chaque optimisation retire. Elle doit
déclarer le port qu'elle sert, et le démarrer sans qu'on le lui demande.

L'exigence qui compte est la dernière, et elle ne se contourne pas :
l'application doit répondre **même sans réseau**. Une image qui installe ses
dépendances au démarrage fonctionne sur votre poste et échoue dans l'usine, le
train ou le centre de calcul dont la sortie Internet est fermée.

## Les repères

- La leçon dit où Docker cherche les instructions, et de quoi un Dockerfile est
  fait : une image de base, des commandes, des fichiers copiés, un port
  déclaré, une commande de démarrage.
- `debian:12` ne contient pas Python. C'est le premier constat à faire, et il
  explique la moitié du Dockerfile.
- Dans un conteneur, `127.0.0.1` ne désigne que le conteneur. Une application
  qui n'écoute que sur sa boucle locale est injoignable depuis l'hôte, même
  avec `-p`.
- Debian 12 protège son Python système : `pip` refuse d'y installer un paquet
  sans qu'on l'y autorise. La leçon dit comment, et pourquoi c'est acceptable
  dans un conteneur dédié à une seule application.

## Vérifier

```bash
dsoxlab check images-premiere-image
```

Sept contrôles. Six lisent l'image construite et ce que l'application répond.
Le septième la lance sans aucun réseau et exige qu'elle réponde quand même.
