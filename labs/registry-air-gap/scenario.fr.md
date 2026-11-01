# Une référence de registre n'est pas une livraison hors ligne

Sur `docker.lab`, `127.0.0.1:15006/catalogue/appli:1.0` n'est disponible que
depuis `dsoxlab-air-gap-registry`. L'environnement destinataire n'aura pas accès
à ce registre. Lui envoyer une référence, un manifeste seul ou un export du
système de fichiers d'un conteneur ne permettra pas de charger et d'exécuter
l'image d'origine.

Préparez une livraison complète dans `/opt/lab-air-gap` :

- `livraison.tar` : une archive Docker contenant l'image publiée, sa
  configuration et toutes ses couches, étiquetée `dsoxlab-air-gap:livree` ;
- `livraison.tar.sha256` : son reçu SHA-256, nommant `livraison.tar` sans
  chemin absolu pour rester portable.

## Mission

Utilisez Skopeo, ou un outil produisant une archive Docker équivalente, pour
récupérer et emballer le produit publié. La livraison doit rester utilisable
après l'arrêt du registre, sans que le cache Docker local comble les manques.
L'image récupérée doit conserver son identité et afficher la release préparée
avec `--network none` et `--pull never`.

Les contrôles copient chaque blob archivé avec le transport répertoire
indépendant de Skopeo, arrêtent le registre d'origine, reconstruisent l'image
depuis ce répertoire, la chargent et l'exécutent sans réseau. Ils restaurent
ensuite le registre. Ni seconde VM ni accès réseau public n'est nécessaire.

Dans ce banc d'emballage seulement, la source est volontairement HTTP sur la
boucle locale ; Skopeo exige `--src-tls-verify=false` pour cette source. Ce n'est
pas une configuration nominale pour un registre en réseau. Ne modifiez ni son
stockage, ni le produit source ou les fichiers du banc ; ne purgez pas Docker
globalement.

Vérifiez le reçu portable depuis le répertoire de livraison :

```bash
cd /opt/lab-air-gap
sha256sum --check livraison.tar.sha256
```
