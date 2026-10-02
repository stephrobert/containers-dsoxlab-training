# 📦 TP5 - Maîtriser les volumes Docker

## 🎯 Objectifs pédagogiques

- Créer et manipuler différents types de volumes Docker.
- Comprendre les différences entre **volume standard**, **bind mount**, et **tmpfs**.
- Monter un volume **NFS** local simulé.
- Appliquer les **bonnes pratiques de nommage, sécurité et nettoyage**.

## 🛠️ Étape 1 - Créer et utiliser un volume standard

1️⃣ Créer un volume nommé `vol_data` :

```bash
docker volume create vol_data
```

2️⃣ Lister les volumes disponibles :

```bash
docker volume ls
```

3️⃣ Lancer un conteneur et écrire un fichier dans ce volume :

```bash
docker run -it --rm -v vol_data:/data alpine sh
echo "Hello from volume" > /data/hello.txt
```

4️⃣ Vérifier que le fichier persiste :

```bash
docker run -it --rm -v vol_data:/data alpine cat /data/hello.txt
```

✅ **Ce que vous observez** : les données dans un volume standard **persistent** même si le conteneur est supprimé.

## 📁 Étape 2 - Utiliser un bind mount

1️⃣ Créez un dossier local `./bind_host_data` :

```bash
mkdir -p bind_host_data
echo "Fichier côté hôte" > bind_host_data/info.txt
```

2️⃣ Lancer un conteneur avec bind mount :

```bash
docker run -it --rm -v $(pwd)/bind_host_data:/app/data alpine sh
```

3️⃣ Depuis le conteneur, affichez le contenu :

```bash
cat /app/data/info.txt
```

✅ **Test** : créez un fichier dans le conteneur, regardez s’il apparaît sur l’hôte.

## ⚡ Étape 3 - Monter un `tmpfs`

1️⃣ Lancer un conteneur avec un volume `tmpfs` :

```bash
docker run -it --rm --tmpfs /tmpfsdata:rw,size=64m alpine sh
```

2️⃣ Écrire un fichier dans ce répertoire :

```bash
echo "temp data" > /tmpfsdata/test.txt
cat /tmpfsdata/test.txt
```

3️⃣ Fermez le conteneur et relancez le même sans volume : les données **n’existent plus**.

✅ **Conclusion** : `tmpfs` est en **mémoire vive uniquement**, parfait pour des données sensibles ou temporaires.

## 🌐 Étape 4 - Monter un volume NFS local (facultatif)

> 💡 Pour cet exercice, vous devez avoir un partage NFS actif sur l’hôte. Vous pouvez utiliser un second conteneur NFS ou un partage local si vous êtes sous Linux.

1️⃣ Créer un volume NFS :

```bash
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=127.0.0.1,nolock,soft,rw \
  --opt device=:/chemin/du/partage/nfs \
  mon_volume_nfs
```

2️⃣ Utiliser ce volume :

```bash
docker run -it --rm -v mon_volume_nfs:/data alpine sh
```

✅ **Test** : écrivez un fichier dans `/data`, vérifiez qu’il est visible sur le serveur NFS.

## 🧹 Étape 5 - Nettoyage et bonnes pratiques

1️⃣ Supprimer les volumes inutilisés (⚠️ supprime toutes les données) :

```bash
docker volume prune
```

2️⃣ Supprimer un volume spécifique :

```bash
docker volume rm vol_data
```

## 🧠 Ce que vous avez appris

Vous avez appris à :

- Créer et utiliser des volumes Docker.
- Comprendre les différences entre les types de volumes.
- Utiliser des bind mounts pour partager des fichiers entre l’hôte et le conteneur.
- Utiliser des volumes `tmpfs` pour des données temporaires.
- Monter un volume NFS pour partager des données entre plusieurs conteneurs.
- Appliquer les bonnes pratiques de nettoyage et de gestion des volumes.
