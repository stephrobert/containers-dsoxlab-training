# Challenge : faire voyager l'API d'inventaire

7 contrôles, 100 points, 30 minutes.

Le projet est dans `challenge/work`. Tout se passe dans un `Dockerfile` que
vous créez à sa racine. Les tests lisent l'image construite et ce que
l'application répond ; ils ne lisent pas vos commandes.

## Le point de départ

| Fichier | Ce qu'il contient |
| --- | --- |
| `app/main.py` | l'API, deux routes : `/health` et `/version`. **Ne pas modifier** |
| `app/requirements.txt` | ses deux dépendances, épinglées. **Ne pas modifier** |

Rien d'autre. Le Dockerfile est à écrire.

## Ce qu'il faut obtenir

1. **L'image part de `debian:12`**, en une seule étape. Le multi-étapes est le
   sujet d'un lab plus loin, et il n'apporterait rien ici.
2. **L'application répond** : `GET /health` rend `200` et `{"status": "ok"}`
   dans un conteneur lancé depuis votre image.
3. **Le port est déclaré** par `EXPOSE`, et c'est celui que l'application
   sert.
4. **Python et les dépendances sont dans l'image** : `python3 --version` et
   `import fastapi, uvicorn` fonctionnent dans le conteneur.
5. **L'image est autonome** : lancée avec `--network none`, l'application
   démarre et se répond à elle-même. Et elle répond toujours avec le réseau.
6. **Un répertoire de travail est déclaré** par `WORKDIR`.
7. **Une commande de démarrage est déclarée**, et elle lance l'application.

## Trois pièges, et ils ont tous une raison

**`debian:12` n'a pas Python.** C'est le premier constat à faire, et il
explique la moitié du Dockerfile. Une image qui l'oublie échoue au démarrage
avec un message qui parle de `$PATH` et non de Python.

**Dans un conteneur, `127.0.0.1` ne désigne que le conteneur.** Une application
qui n'écoute que sur sa boucle locale est injoignable depuis l'hôte, même avec
`-p`. Le contrôle 2 échouera sans que le journal du conteneur montre quoi que
ce soit d'anormal : l'application tourne, elle n'est juste joignable par
personne.

**Debian 12 refuse que `pip` installe dans son Python système.** Le message
parle d'`externally-managed-environment` et renvoie à la PEP 668. Deux
réponses existent, la leçon jumelée les donne toutes les deux, et l'une est
légitime dans un conteneur dédié à une seule application.

## Le contrôle 5 est celui qui compte

Les six autres passent avec une image qui installe ses dépendances au
démarrage. Le cinquième la lance sans aucun réseau et exige qu'elle réponde
quand même.

Ce n'est pas une sévérité gratuite : c'est la panne que le scénario raconte.
Une image qui télécharge au démarrage fonctionne sur votre poste et échoue
partout où la sortie Internet est fermée, c'est-à-dire dans la plupart des
environnements de production.

## Vérifier

```bash
dsoxlab check images-premiere-image
```

Le premier `check` construit l'image, ce qui prend une quinzaine de secondes.
Les suivants réutilisent le cache de build et durent quelques secondes.

Bloqué ? `dsoxlab hint images-premiere-image`.
