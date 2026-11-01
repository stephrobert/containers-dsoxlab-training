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
