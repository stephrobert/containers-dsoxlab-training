# Un digest n'identifie pas son auteur

L'équipe exporte son image de conteneur dans une archive. Une somme détecte
les octets modifiés, mais leur auteur peut publier une nouvelle somme.
La porte de livraison exige un auteur authentifié, pas une étiquette « signé ».

Un administrateur local a approuvé une CA de signature et une identité de
livraison. L'archive et une signature détachée sont prêtes ; le vérificateur
refuse tout car l'implémentation de sa politique manque.

Implémentez une porte qui accepte le signataire approuvé et refuse un
signataire valide d'une autre identité, une clé étrangère et un contenu
altéré. Travaillez sur `docker.lab` dans `/opt/lab-image-signature`.
Consultez [les exigences](challenge/README.fr.md).

## Mission : accepter seulement le signataire de livraison approuvé

Travaillez sur `docker.lab` dans `/opt/lab-image-signature`, pas dans le
challenge/work local. La fixture fournit `archive.tar`, `archive.sig`,
`keys/approved.crt`, les clés privées synthétiques générées à l'exécution
et les entrées de confiance de l'administrateur.

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

`dsoxlab check images-signature-identite` génère de vraies signatures
positives et négatives neuves. `dsoxlab clean images-signature-identite`
retire l'archive, les clés générées et seulement les images ajoutées par ce lab.
