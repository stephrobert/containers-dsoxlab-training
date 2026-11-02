# compose-profils-et-variantes

**Public :** l'apprenant.

Un fichier d'entrée déclare, une configuration effective décide. Ce lab fait
mesurer l'écart, sur le cas qui coûte le plus cher : un montage de
développement oublié en déploiement.

## Ce que vous saurez faire

- Dériver deux variantes d'un même fichier de base, sans jamais le modifier.
- Lire la **configuration effective** plutôt que le fichier d'entrée, et dire
  pourquoi c'est la seule lecture qui vaut.
- Reconnaître un montage de développement actif en déploiement, et le cas
  particulièrement sournois où il ne monte rien du tout.
- Tenir un service optionnel hors de la résolution par un profil, et le faire
  apparaître à la demande.

## Comment c'est noté

Quatre contrôles de poids égal :

1. la variante de déploiement **tourne**, sans aucun montage, et sert la version
   de l'image ;
2. la variante de développement monte bien les sources, vérifié dans la
   configuration effective **et** à l'exécution ;
3. le fichier de base ne porte aucun montage, et la variante de déploiement
   n'en déclare aucun ;
4. le service optionnel est absent sans son profil, et présent avec.

L'appareil de mesure est l'écart entre deux versions : l'image porte la sienne,
le disque en porte une autre. La réponse du service dit lequel des deux il lit.

## Ce que le lab ne fait pas

Il ne vous impose aucune mécanique de dérivation. `include`, `extends`,
plusieurs `-f`, un `COMPOSE_FILE` : tout convient, parce que le contrôle lit le
résultat et non la méthode.
