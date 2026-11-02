# Scénario

Le service de référence de l'équipe tourne sur `docker.lab`, déployé par
Compose, épinglé par digest, avec son volume de données. Il garde des
enregistrements, et il en porte déjà un : la production n'a pas attendu votre
arrivée.

Trois releases sont disponibles, et on vous donne leurs digests. La `2.0` est
une évolution de routine. La `3.0`, elle, **migre le schéma de l'état**, et
c'est écrit dans ses notes de version, en une ligne que personne ne lit.

La veille de la mise en production, votre responsable pose la seule question qui
compte : « si ça se passe mal, on revient en arrière ? »

Vous répondez oui. C'est vrai pour la `2.0`. Ce ne l'est plus après la `3.0`, et
personne dans l'équipe ne sait dire à partir de quel moment exactement.

## Mission

Déployez la `2.0` par son digest, écrivez un enregistrement, revenez à la `1.0`
sans rien perdre. Déployez ensuite la `3.0`, puis **établissez** que le retour
en arrière n'est plus possible, et consignez ce que la machine vous répond.

Le détail de ce qui est attendu, et le format du constat, sont dans
`/opt/lab-retour/MISSION.md`.
