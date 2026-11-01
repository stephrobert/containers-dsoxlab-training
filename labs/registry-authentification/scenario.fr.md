# TLS ne rend pas un registre privé

Sur `docker.lab`, `registry-auth.lab.test:15445` sert déjà HTTPS vérifié.
Sa CA est installée pour Docker, mais tout client du réseau privé des VM peut
télécharger ou publier sans identifiants. TLS protège le transport ; il ne
décide pas qui peut utiliser le registre.

`/opt/lab-registry-auth` contient :

- `config.yml`, monté dans `/etc/docker/registry/config.yml` ;
- `auth/`, monté dans `/auth`, initialement vide ;
- `certs/`, monté dans `/certs`, avec l'identité TLS fournie ;
- `data/`, le stockage existant des images ;
- `credentials.env`, le compte `publisher` et son mot de passe tiré au setup ;
- `client/`, un répertoire de configuration Docker dédié, initialement vide ;
- `appli/`, les sources du produit déjà publié `catalogue/appli:1.0`.

## Mission

- Configurez le fournisseur `htpasswd` du registre avec les identifiants
  fournis. Son fichier de mots de passe doit utiliser bcrypt, pris en charge
  par cette version du registre.
- Redémarrez `dsoxlab-auth-registry` sans perdre TLS ni les images stockées.
- Les requêtes anonymes sur l'API, les manifestes et les uploads doivent rendre
  `401` avec un challenge HTTP Basic. Les mauvais identifiants rendent aussi
  `401` ; le compte fourni doit réussir.
- Enregistrez une connexion avec
  `docker --config /opt/lab-registry-auth/client login`. Utilisez
  `--password-stdin`, pas le mot de passe dans un argument de commande.
- Avec ce client, tirez `registry-auth.lab.test:15445/catalogue/appli:1.0`
  et prouvez qu'un produit neuf peut être poussé puis tiré.

Utilisez sudo pour le fichier d'identifiants protégé et la configuration hôte.
Ne modifiez ni les identifiants Docker globaux, ni les certificats, les sources
du produit ou la résolution de nom. `insecure-registries` et les contournements
TLS ne conviennent pas. Les contrôles exercent de vraies opérations sous HTTPS
vérifié, y compris le refus du pull Docker lorsque sa CA privée est
temporairement retirée.

Le chemin du fichier est celui dans le conteneur : `/auth/htpasswd`, pas le
répertoire de travail hôte. Un curl authentifié ne connecte pas Docker.
