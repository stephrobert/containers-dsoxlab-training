# La boutique ne trouve plus son catalogue

## La situation

Vendredi, deux équipes ont déployé leurs services sur la même machine, chacune
de son côté, chacune avec ses propres commandes. Lundi matin, la boutique en
ligne affiche une page d'erreur : elle ne trouve plus son catalogue.

Le conteneur de la base tourne. Le conteneur de l'application tourne. Les deux
répondent quand on les interroge de l'intérieur. Et pourtant l'application ne
joint rien.

L'audit hebdomadaire, arrivé le même matin, ajoute une ligne sans rapport
apparent : **la base de données est joignable depuis l'extérieur**.

## Ce qui est en place

```text
boutique    l'application. Elle cherche sa base sous le nom `base`, en dur
            dans sa configuration, et ce nom ne peut pas changer.

catalogue   la base. Elle écoute sur son port 80 et répond un jeton.
```

Les deux sont bâtis sur l'image `lab-diagnostic:1.0`.

## Ce qui est attendu à la fin

1. Depuis `boutique`, le nom `base` se résout vers une adresse que `catalogue`
   porte réellement.
2. Depuis `boutique`, une connexion sur `base` port 80 rend le jeton.
3. `catalogue` ne publie **aucun** port.
4. Depuis `boutique`, le nom `catalogue` se résout **aussi** : l'exploitation
   doit continuer à désigner le conteneur par son nom réel.
5. Gardez l'image fournie et le volume `dsoxlab-diagnostic-data` sur `/data`.
   Installez `/opt/lab-diagnostic/recreate.sh` exécutable sans argument :
   il remplace réellement `catalogue` sans perdre la valeur nouvelle écrite
   dans `/data/jeton`. Le remplaçant sert cette valeur exacte depuis `boutique`
   et reste non exposé. Tout réseau ajouté porte
   `dsoxlab.lab=reseau-diagnostic-dns` ; aucun prune global.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## C'est une épreuve

**Rien ne vous sera réexpliqué.** Les labs réseau du parcours ont enseigné ce
qu'il faut savoir : le réseau par défaut et ses limites, un réseau dédié et sa
résolution de noms, la publication de ports et ses trois postures. Celle-ci
mesure.

Cinq contrôles de poids égal, **75 points pour réussir**, et tout est noté sur
l'état réel du moteur. Les messages des contrôles nomment le symptôme, pas le
geste : c'est à vous de faire le lien.
La conservation des données est critique dans le parcours : le seuil
numérique seul ne remplace pas la réussite de cette exigence.

Quatre indices existent, du plus vague au plus explicite, et ils coûtent des
points.

## Deux conseils qui ne sont pas des indices

Gardez les **noms** des conteneurs : les contrôles les cherchent nommément, et
le quatrième point vous dit déjà pourquoi.

Et ne vous contentez pas d'une connexion qui aboutit pour conclure qu'un service
répond. Le proxy de Docker accepte une connexion avant que quoi que ce soit
n'écoute : lisez la réponse. C'est vrai dans ce lab comme dans votre
production.
