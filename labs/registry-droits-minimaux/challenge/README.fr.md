# Des identifiants ne sont pas des permissions

## La situation

L'équipe de livraison a un registre en TLS et deux comptes valides, et aucun des
deux ne peut distribuer une image. Donner tous les droits aux deux rétablirait
la livraison, et ferait de la machine de déploiement un éditeur.

## Mission

Travaillez dans `/opt/lab-registry-rights`, sur les VM. L'éditeur est sur
`docker.lab`, le lecteur sur `docker-client.lab`. Le registre écoute sur
`registry-rights.lab.test:15447`, le service de jetons sur le port `15448`. TLS
est prêt. Les mots de passe sont dans `credentials.json` sur `docker.lab`, à lire
avec `sudo`. La seule chose à réparer est `auth.yml`, sur `docker.lab`.

### 1. L'éditeur publie

Le compte `publisher` tire et pousse `catalogue/appli`. Rechargez ensuite le
conteneur `dsoxlab-registry-droits-minimaux-auth`. Le contrôle construit une
image neuve depuis le `Dockerfile` fourni, la pousse, et attend un digest.

### 2. Le lecteur tire, et ne publie pas

Depuis `docker-client.lab`, le compte `reader` tire ce digest. L'identifiant de
l'image et sa sortie sans réseau sont ceux de l'éditeur. Le push d'un contenu
neuf par `reader` est refusé pour manque de droits, et sans la CA du lab, le pull
échoue.

### Ce que les deux contrôles exigent aussi

- `reader` ne peut pas ouvrir d'envoi, même en demandant `pull,push`.
- Aucun des deux comptes ne lit ni n'écrit dans un autre dépôt.
- L'accès anonyme et les mauvais mots de passe sont refusés.
- TLS reste vérifié sur les deux machines : pas d'`insecure-registry`.

Pour vos essais, rangez les identifiants dans un dossier à part, avec
`docker --config`, sous `/opt/lab-registry-rights`. `dsoxlab clean` remet les deux
machines dans leur état d'avant.
