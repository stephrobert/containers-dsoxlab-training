# 🐳 00 - Manipulez des images de conteneurs

Ce dossier vous guide pas à pas pour construire et exécutez une image Docker de
plus en plus complexe et sécurisée, basée sur une API minimale développée en
Python avec FastAPI.

L'objectif est de maîtriser les bonnes pratiques de construction d'image :

- d'abord sur une base **Debian 12**,
- puis migrer vers **Alpine Linux** pour gagner en compacité,
- tout en appliquant petit à petit les bonnes pratiques de **sécurité** et
  d'optimisation :
  - minimisation de la surface d'attaque,
  - optimisation de la taille finale de l'image
  - suppression du compte root,
  - limitation des capabilities.

## 🎯 Prérequis pour suivre ce TP

- [**Compétences en ligne de
  commande**](https://www.stephane-robert.info/docs/admin-serveurs/linux/introduction/)
  :
  - Être à l’aise avec un terminal Linux.
  - Connaître les commandes de base (`ls`, `cd`, `mkdir`, `rm`, etc.).
  - Savoir utiliser un éditeur de texte en ligne de commande (`nano`, `vim`,
    etc.). Pouquoi pas essayer
    [vscode](https://www.stephane-robert.info/docs/developper/autres-outils/ide/visual-studio-code/)
    ?

- [**Notions de base sur les
  conteneurs**](https://www.stephane-robert.info/docs/conteneurs/)
  :
  - Comprendre le principe d’un **conteneur**.
  - Savoir à quoi sert une **image Docker** et comment elle est construite.

- **Un environnement de développement fonctionnel** :
  - Un système **Linux, macOS, ou Windows avec WSL**.
  - L’installation de **Docker** (et `docker` utilisable depuis le terminal).
  - L’installation de **Python 3** et `pip`.

## 🎯 Objectifs pédagogiques

À travers ces exercices, vous apprendrez à :

- 🏗️ Construire des images Docker à partir de différentes bases.
- 📦 Optimiser la taille des images et réduire la surface d'attaque.
- 🛡️ Analyser et améliorer la sécurité des images Docker.
- 🔄 Utiliser des techniques avancées comme les constructions multi-étapes.

## 🗂️ Structure du projet

- `01-debian12-basique/` : 🐧 Création d'une image Docker basique basée sur
  Debian 12.
- `02-debian12-optimisee/` : 📉 Optimisation de l'image Debian 12 en réduisant
  sa taille avec un fichier `.dockerignore`.
- `03-alpine/` : 🏔️ Migration vers une image Alpine Linux pour une empreinte
  plus légère et analyse des images avec Trivy.
- `04-multistage-build/` : 🏗️ Mise en œuvre d'une construction multi-étapes
  pour optimiser la taille et la sécurité de l'image finale.
- `05-volumes/` : 📦 Utilisation de volumes Docker pour la persistance des
  données et la gestion des fichiers de configuration.

## 📖 Instructions générales

Chaque dossier contient :

- 📂 Un sous-dossier `app/` avec le code source de l'application FastAPI.
- 📄 Un `Dockerfile` spécifique à l'étape concernée.
- 📝 Un fichier `README.md` détaillant les objectifs, les instructions de
  construction et d'exécution, ainsi que les points d'apprentissage spécifiques.

Pour chaque étape, consultez le fichier markdown pour des instructions
détaillées.

N'hésitez pas à explorer chaque dossier dans l'ordre pour construire
progressivement vos compétences en matière de conteneurisation et de
sécurisation des applications Docker.
