# Une somme n'identifie pas son auteur

## La situation

L'équipe livre son image de conteneur dans une archive. Une somme détecte des
octets changés, mais celui qui les change peut publier une nouvelle somme. La
livraison exige donc un auteur authentifié.

Sur `docker.lab`, `/opt/lab-image-signature` contient `archive.tar`,
`archive.sig`, `keys/approved.crt`, des clés privées d'essai, et ce que
l'administrateur approuve : `trust/ca.crt` et `trust/policy.json`. Le vérificateur
`verify.py` refuse tout, car sa politique n'est pas écrite.

## Mission

1. Implémentez `verify.py ARCHIVE SIGNATURE CERTIFICAT`. Rendez 0 seulement si
   la signature fournie authentifie ces octets exacts avec la clé publique
   d'un certificat valide rattaché à `trust/ca.crt`. Rendez 1 pour un refus
   explicite ou une entrée invalide.
2. Appliquez l'URI d'identité exacte de `trust/policy.json` :
   `spiffe://dsoxlab/release/builder`, avec SHA-256. Préservez les entrées de
   confiance. Un certificat valide pour la CA mais d'une autre identité
   n'est pas un signataire approuvé.
3. Acceptez l'archive de conteneur authentique et du contenu neuf réellement
   signé par la clé approuvée. Ne reconnaissez ni noms de fichiers, ni texte
   console, ni somme d'une fixture fixe à la place de la cryptographie.
4. Refusez les octets altérés, une signature produite par une autre clé
   privée et un certificat auto-émis revendiquant l'URI approuvé.
   Validation de chaîne, politique d'identité exacte et vérification de
   signature des octets sont toutes nécessaires.
5. Gardez les clés privées dans la VM et hors du contrôle de version.
   Utilisez seulement le répertoire et l'image étiquetée du lab.
   N'ajoutez pas de scanner et ne revendiquez ni Sigstore, ni signature
   sans clé, ni journal de transparence.

Trois contrôles fabriquent de nouvelles signatures, bonnes et mauvaises, à chaque
passage.
