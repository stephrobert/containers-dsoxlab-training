# 🏔️ TP3 - Migration vers Alpine Linux

## 🎯 Objectifs

- Remplacer une image de base Debian par **Alpine Linux**.
- Adapter l'installation de Python et des dépendances avec `apk`.
- Réduire significativement la taille de l’image.
- Vérifier que l’API FastAPI fonctionne toujours correctement.
- Comparer les tailles des images obtenues.

👉 Ce TP fait suite à [`02-debian12-optimisee`](../02-debian12-optimisee).

## 📁 Structure du projet

```bash
03-alpine/
├── app/
│   ├── main.py
│   └── requirements.txt
├── .dockerignore
├── Dockerfile
```

## 🛠️ Étape 1 - Modifier l'image de base

Dans le nouveau `Dockerfile`, remplacez :

```dockerfile
FROM debian:12
```

par :

```dockerfile
FROM alpine:3.18
```

## 🧰 Étape 2 - Installer Python et pip avec `apk`

Remplacez l’installation APT par `apk`, le gestionnaire de paquets Alpine :

```dockerfile
RUN apk add --no-cache python3 py3-pip
```

🧠 `--no-cache` évite de conserver les fichiers d’index d’installation.

## 📝 Dockerfile complet (version Alpine minimale)

```dockerfile
# Image de base
FROM alpine:3.18

# Copie de l’application dans le conteneur
WORKDIR /app
COPY app/ /app/

# Installation de Python 3 et pip
RUN apk add --no-cache python3 py3-pip && \
    pip3 install --break-system-packages -r requirements.txt

# Exposition du port de l’API
EXPOSE 8000

# Commande de démarrage de l’API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Étape 3 - Build et test

```bash
docker build -t fastapi-alpine .
```

🎯 Vérifiez que l’image est bien construite :

```bash
docker images | grep fastapi

fastapi-alpine     latest    ad9c28e9ae3e   16 seconds ago   116MB
fastapi-optimise   v4        bb2121d01538   9 minutes ago    236MB
fastapi-optimise   v1        d1c77c5394e7   25 minutes ago   256MB
fastapi-optimise   v2        ac5a57858d17   26 minutes ago   236MB
fastapi-optimise   v3        ac5a57858d17   26 minutes ago   236MB
fastapi-auto       latest    7e2e921dad53   32 minutes ago   678MB
```

🎯 L’image est **bien plus petite** que l’image Debian.

Lancez le conteneur :

```bash
docker run -d -p 8000:8000 fastapi-alpine
```

Vérifiez que l’API fonctionne :

```bash
curl http://localhost:8000/health

{"status":"ok"}
```

Ca fonctionne ! 🎉

## ⚖️ Étape 4 - Vérification des vulnérabilités

Vérifiez les vulnérabilités de l’image Debian avec Trivy :

```bash
trivy image --severity HIGH,CRITICAL fastapi-optimise:v4

┌───────────┬────────────────┬──────────┬──────────────┬───────────────────┬───────────────┬─────────────────────────────────────────────────────────────┐
│  Library  │ Vulnerability  │ Severity │    Status    │ Installed Version │ Fixed Version │                            Title                            │
├───────────┼────────────────┼──────────┼──────────────┼───────────────────┼───────────────┼─────────────────────────────────────────────────────────────┤
│ libexpat1 │ CVE-2023-52425 │ HIGH     │ affected     │ 2.5.0-1+deb12u1   │               │ expat: parsing large tokens can trigger a denial of service │
│           │                │          │              │                   │               │ https://avd.aquasec.com/nvd/cve-2023-52425                  │
│           ├────────────────┤          ├──────────────┤                   ├───────────────┼─────────────────────────────────────────────────────────────┤
│           │ CVE-2024-8176  │          │ will_not_fix │                   │               │ libexpat: expat: Improper Restriction of XML Entity         │
│           │                │          │              │                   │               │ Expansion Depth in libexpat                                 │
│           │                │          │              │                   │               │ https://avd.aquasec.com/nvd/cve-2024-8176                   │
├───────────┼────────────────┤          ├──────────────┼───────────────────┼───────────────┼─────────────────────────────────────────────────────────────┤
│ perl-base │ CVE-2023-31484 │          │ affected     │ 5.36.0-7+deb12u1  │               │ perl: CPAN.pm does not verify TLS certificates when         │
│           │                │          │              │                   │               │ downloading distributions over HTTPS...                     │
│           │                │          │              │                   │               │ https://avd.aquasec.com/nvd/cve-2023-31484                  │
├───────────┼────────────────┼──────────┼──────────────┼───────────────────┼───────────────┼─────────────────────────────────────────────────────────────┤
│ zlib1g    │ CVE-2023-45853 │ CRITICAL │ will_not_fix │ 1:1.2.13.dfsg-1   │               │ zlib: integer overflow and resultant heap-based buffer      │
│           │                │          │              │                   │               │ overflow in zipOpenNewFileInZip4_6                          │
│           │                │          │              │                   │               │ https://avd.aquasec.com/nvd/cve-2023-45853                  │
└───────────┴────────────────┴──────────┴──────────────┴───────────────────┴───────────────┴─────────────────────────────────────────────────────────────┘
```

Faisons de même avec l’image Alpine :

```bash
trivy image --severity HIGH,CRITICAL fastapi-alpine
```

🎯 L'image Alpine ne contient à ce jour aucune vulnérabilité !

## 🧠 Ce que vous avez appris

Vous avez appris à :

- Migrer une image Docker de Debian vers Alpine Linux.
- Installer Python et ses dépendances avec `apk`.
- Réduire la taille de l'image Docker.
- Vérifier la sécurité de l'image avec Trivy.
- Comparer les vulnérabilités entre Debian et Alpine.
