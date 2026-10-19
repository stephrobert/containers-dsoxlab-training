# TP1 - Image Docker basique avec Debian 12

## 🎯 Objectifs

- Comprendre comment construire une **image Docker** à partir de **Debian 12**.
- Containeriser une **application FastAPI minimale**.
- Apprendre les bases du `dockerfile` et du processus de build.
- Lancer et tester un conteneur localement.

👉 Avant de commencer, assurez-vous d’avoir Docker installé sur votre machine :
📘 [Guide d'installation de
Docker](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/)

## 🔰 Étape 1 - Démarrer depuis une image de base

1️⃣ **Télécharger et exécuter une image Debian en mode interactif** :

```bash
docker run -it debian:12 bash
```

📌 Vous êtes maintenant **dans un shell Debian** à l’intérieur d’un conteneur
éphémère.

2️⃣ **Vérifiez que Python n’est pas installé** :

```bash
python3 --version

bash: python3: command not found
```

✋ Résultat attendu : erreur → vous allez devoir l’installer.

## 🔧 Étape 2 - Installer Python et pip à la main

1️⃣ **Dans le conteneur** :

```bash
apt-get update
apt-get install -y python3 python3-pip
```

2️⃣ **Vérifiez que Python fonctionne** :

```bash
python3 --version
pip3 --version
```

✅ Vous avez maintenant un environnement Python prêt. Il est temps de commencer à
écrire votre premier `dockerfile` !

## 🛠️ Étape 3 - Commencer à écrire le dockerfile

Maintenant que vous avez testé manuellement ce qu’il faut pour faire fonctionner
votre application Python dans un conteneur Debian, vous allez commencer à écrire
votre **dockerfile**.

📌 Créez un fichier appelé `dockerfile` à la racine de votre projet, à côté du
dossier `app/`.

### 🧱 1. Définir l’image de base

```dockerfile
FROM debian:12
```

🧠 Cela signifie : On part d’un système Debian 12 minimal comme fondation.

### ⚙️ 2. Installer Python et pip

Ajoutez ces lignes pour installer les outils nécessaires :

```dockerfile
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

🧠 Décomposition :

- `apt-get update` → met à jour la liste des paquets.
- `apt-get install` → installe Python 3 et pip.
- `apt-get clean` & `rm` → suppriment les fichiers temporaires pour **réduire la
  taille** de l’image.

### 🔄 Test intermédiaire

💡 À ce stade, testons l’image !

1️⃣ Construisez-la :

```bash
docker build -t base-python .
```

2️⃣ Lancez un conteneur :

```bash
docker run -it base-python bash
```

3️⃣ Testez dans le conteneur :

```bash
python3 --version
pip3 --version
```

✅ Si tout fonctionne, vous venez de créer une **image Debian avec Python 3
fonctionnel**. Maintenant, il est temps d’ajouter votre application FastAPI.

## 📥 Étape 4 - Ajouter l'application dans l’image

Maintenant que votre image Debian contient Python et pip, vous allez y **ajouter
le code source de l’application FastAPI**, et installer ses dépendances.

📌 L’objectif de cette étape est de **copier les fichiers** dans l’image et de
les **préparer à l’exécution**.

### 🗂️ 1. Structure attendue du projet

Voici comment sont organisés vos fichiers :

```bash
01-debian12-basique/
├── app/
│   ├── main.py
│   └── requirements.txt
└── dockerfile
```

✅ Vérifiez bien que vous avez un dossier `app/` contenant :

- `main.py` : votre API FastAPI minimale
- `requirements.txt` : liste des dépendances Python (`fastapi`,
  `uvicorn[standard]`)

### ✍️ 2. Ajouter les instructions dans le dockerfile

Ajoutez ces lignes **sous les précédentes** :

```dockerfile
# Définir le répertoire de travail
WORKDIR /app

# Copier le code de l’application dans l’image
COPY app/ /app/
```

🧠 Cela signifie :

- `WORKDIR /app` → on place notre point de travail à `/app` dans l’image.
- `COPY app/ /app/` → on copie le dossier `app/` de notre machine locale vers
  `/app/` dans le conteneur.

### 📦 3. Installer les dépendances Python

Ajoutez juste après :

```dockerfile
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt
```

🧠 Cela installe les packages Python requis dans l’image, de façon optimisée
(sans cache pip inutile).

### 🔄 Test intermédiaire

1️⃣ **Rebuild de l’image** :

```bash
docker build -t fastapi-app-base .
```

2️⃣ **Lancement en interactif** pour tester** :

```bash
docker run -it fastapi-app-base bash
```

3️⃣ **Depuis le shell du conteneur** :

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

🌍 Dans un autre terminal (sur votre machine hôte), testez si le service répond
:

```bash
curl http://localhost:8000/health
```

❌ Si ça ne marche pas, c’est normal : on n’a pas encore publié le port avec `-p`
➡️ On verra ça **dans l'étape suivante** quand on automatisera le lancement.

## 🚀 Étape 5 - Automatiser le lancement de l'application

Jusqu’à présent, vous avez lancé manuellement `uvicorn` depuis un terminal dans
le conteneur. ➡️ L’objectif de cette étape est de **faire en sorte que le
conteneur lance automatiquement l’API au démarrage**, sans intervention
manuelle.

### 🧾 1. Ajouter une commande de démarrage avec `CMD`

Ajoutez cette ligne **à la fin du dockerfile** :

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

🧠 Que fait cette ligne ?

- Elle indique à Docker que, lorsque le conteneur démarre, il doit **exécuter ce
  programme**.
- `--host 0.0.0.0` permet d’écouter **sur toutes les interfaces réseau** du
  conteneur (sinon, l'API ne sera pas accessible de l’extérieur).
- `--port 8000` correspond au port d’écoute du serveur.

### 🔁 2. Rebuild de l’image

Chaque fois que vous modifiez le `dockerfile`, vous devez reconstruire l’image :

```bash
docker build -t fastapi-auto .
```

### 🧪 3. Lancer le conteneur avec publication du port

Utilisez `-p 8000:8000` pour exposer le port du conteneur sur votre machine hôte
:

```bash
docker run -d -p 8000:8000 fastapi-auto
```

> `-d` signifie "détaché" (le conteneur tourne en arrière-plan)

### 🔍 4. Vérifier que l’API fonctionne

Dans un autre terminal, testez avec `curl` :

```bash
curl http://localhost:8000/health
```

✅ Vous devez recevoir une réponse comme :

```json
{"status":"ok"}
```

## 🧱 Étape 6 - Comprendre le fonctionnement des images Docker

Jusqu’à présent, vous avez construit et utilisé des images Docker sans trop vous
soucier de **ce qui se passe à l’intérieur**. Cette étape vous aide à
**visualiser** comment Docker fonctionne réellement, et à **maîtriser les
commandes de base** pour travailler efficacement avec les images et conteneurs.

### 📚 1. Comment fonctionne une image Docker ?

Une image Docker est composée de **couches** (layers). Chaque instruction du
`dockerfile` (comme `RUN`, `COPY`, etc.) crée une **nouvelle couche**.

🧠 Ces couches sont :

- **Empilées** pour constituer l'image finale.
- **Mises en cache** pour accélérer les reconstructions.
- **Partagées** entre plusieurs images pour économiser de l’espace disque.

### 🔍 2. Lister les images et leurs tailles

La commande de base :

```bash
docker images
```

🔍 Exemple de sortie :

```bash
REPOSITORY         TAG       IMAGE ID       CREATED         SIZE
fastapi-auto       latest    a1b2c3d4e5f6   10 minutes ago  230MB
debian             12        abc123456789   3 weeks ago     28MB
```

🧠 **Colonne "SIZE"** :
C’est la **taille totale de l’image**, **toutes couches confondues**, une fois
construite.

### 📦 3. Inspecter en détail une image

```bash
docker image inspect fastapi-auto
```

Cette commande retourne un **JSON** très complet. Pour n’afficher que la taille
brute :

```bash
docker image inspect fastapi-auto --format='{{.Size}}'
```

➡️ La taille est donnée en **octets**. Par exemple, `646989230` = **~241 Mo**

💡 Pour la lire facilement, vous pouvez passer par `numfmt` :

```bash
docker image inspect fastapi-auto --format='{{.Size}}' | numfmt --to=iec
618Mo
```

### 🔍 4. Inspecter les couches avec `dive`

📦 `dive` est un outil très pratique pour **explorer visuellement les couches**
d’une image Docker. Plus d'infos sur
[dive](https://www.stephane-robert.info/docs/conteneurs/outils/dive/)

#### 🛠️ Installer `dive`

```bash
sudo snap install dive        # si disponible
# ou sinon via script ou binaire : https://github.com/wagoodman/dive
```

#### ▶️ Utiliser dive

```bash
dive fastapi-auto
```

🔍 Ce que vous allez voir :

- Les couches créées à chaque instruction (`FROM`, `RUN`, `COPY`, etc.).
- Les fichiers ajoutés, modifiés, supprimés.
- Une estimation de l’efficacité de votre image (taille, redondances, etc.).

### 🧰 5. Commandes utiles pour gérer les images et conteneurs

#### 📋 Lister les images

```bash
docker images
```

#### 🧹 Supprimer une image

```bash
docker rmi fastapi-auto
```

🔺 Attention : une image ne peut pas être supprimée si un conteneur l’utilise
encore.

#### 🚛 Lister les conteneurs

```bash
docker ps          # conteneurs en cours d'exécution
docker ps -a       # tous les conteneurs (actifs ou arrêtés)
```

#### 🛑 Stopper et supprimer un conteneur

```bash
docker stop <id>
docker rm <id>
```

#### 🧹 Nettoyer tout ce qui est inutile

```bash
docker system prune -a
```

🔺 Supprime **toutes les images non utilisées**, les conteneurs arrêtés, et les
volumes anonymes. À utiliser avec prudence.

## 🧠 Ce que vous avez appris

Vous avez appris à :

- Créer une image Docker à partir de Debian 12.
- Installer Python et pip dans l’image.
- Ajouter une application FastAPI et ses dépendances.
- Lancer l’application automatiquement au démarrage du conteneur.

## 🎯 **Bonus : Challenge**

- Testez une version modifiée de votre `dockerfile` sans nettoyage (`apt-get
  clean`, etc.)
- Comparez la taille avec `docker images`
- Lancez `dive` sur les deux versions pour visualiser l’impact
