# epreuve-livrer-une-image

**Public :** l'apprenant.

Une image n'est livrée que si une autre machine, qui n'a rien de la vôtre, peut
la faire tourner. Cette épreuve le fait prouver, et vérifie en même temps que le
secret de construction n'a survécu nulle part.

## Ce que vous saurez faire

- Employer un secret pendant une construction sans qu'il entre dans une couche,
  et dire pourquoi un argument de construction ou une variable d'environnement
  n'en sont pas capables.
- Publier dans un registre privé en TLS vérifié, avec le compte qui en a le
  droit.
- Désigner une livraison par son digest, et dire ce qu'une étiquette ne garantit
  pas.
- Faire tourner cette livraison depuis un client nu, en lecture seule.
- Vérifier qu'un compte en lecture seule ne peut pas publier, et savoir que
  repousser une image déjà présente ne le vérifie pas.

## Comment c'est noté

Quatre contrôles de poids égal, seuil de réussite **75 %** :

1. la livraison est publiée, et la référence consignée porte le digest que le
   registre sert ;
2. l'empreinte consignée est celle du secret de ce passage, et le secret ne se
   trouve ni dans l'historique, ni dans aucune couche ;
3. le conteneur tourne sur le **client nu**, sur la référence par digest, et
   répond l'empreinte ;
4. le compte en lecture seule se voit refuser une session d'envoi par le
   registre.

Les deux hôtes sont interrogés séparément : une image qui ne tourne que sur la
machine qui l'a construite n'est pas livrée.

## Ce que l'épreuve ne fait pas

Elle n'impose ni le nombre d'étapes de votre construction, ni la façon de monter
le secret. Le contrôle lit l'image produite et l'état des deux machines.
