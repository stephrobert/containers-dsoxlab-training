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
   Installez `/opt/lab-remise-en-service/recreate.sh` exécutable sans argument :
   il remplace réellement `catalogue` sans perdre la valeur nouvelle écrite
   dans `/data/jeton`. Le remplaçant sert cette valeur exacte depuis `boutique`
   et reste non exposé. Tout réseau ajouté porte
   `dsoxlab.lab=remettre-un-conteneur-en-service` ; aucun prune global.

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

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service.

```text
boutique    l'application. Elle cherche sa base sous le nom `base`, en dur
            dans sa configuration, et ce nom ne peut pas changer.

catalogue   la base. Elle écoute sur son port 80 et répond un jeton.
```

Les deux tournent, les deux répondent quand on les interroge de l'intérieur, et
l'application ne joint rien. L'audit signale par ailleurs que la base est
joignable depuis l'extérieur.

### Les cinq contrôles

**1. Depuis `boutique`, le nom `base` se résout**, vers une adresse que
`catalogue` porte réellement.

Un nom qui pointe ailleurs est pire que pas de nom : l'application parlerait à
autre chose.

**2. Depuis `boutique`, une connexion sur `base` port 80 rend le jeton.**

Ce contrôle est séparé du premier parce que leurs causes sont différentes :
résoudre n'est pas joindre.

**3. `catalogue` ne publie aucun port.**

C'est la ligne de l'audit. Une base n'a aucune raison d'être joignable depuis
l'extérieur : son application l'atteint par le réseau des conteneurs.

**4. Depuis `boutique`, le nom `catalogue` se résout aussi.**

L'exploitation doit continuer à désigner le conteneur par son nom réel. C'est
une exigence, pas un détail : l'application a son nom à elle, l'exploitation
garde le sien.
**5. Le remplacement réel conserve la donnée métier nouvelle.**

Gardez l'image fournie et `dsoxlab-diagnostic-data` sur `/data`.
Installez `/opt/lab-remise-en-service/recreate.sh` : le nouveau conteneur sert la
valeur nouvelle de `/data/jeton` via le chemin corrigé, sans exposition.
Tout réseau ajouté porte `dsoxlab.lab=remettre-un-conteneur-en-service` ; aucun prune global.

### C'est une épreuve

**Rien ne vous sera réexpliqué.** Les cinq labs réseau du parcours ont enseigné
ce qu'il faut savoir. Celle-ci mesure.

Cinq contrôles de poids égal, **75 points pour réussir**. Les messages des
contrôles nomment le symptôme, jamais le geste : faire le lien est le travail.
Le seuil numérique n'annule pas la conservation critique des données du parcours.

Quatre indices existent, du plus vague au plus explicite, et ils coûtent des
points. Le dernier nomme les fautes qui laissent croire au succès.

### Deux choses qui ne sont pas des indices

Gardez les **noms** des conteneurs : les contrôles les cherchent nommément, et
le quatrième point vous dit déjà pourquoi.

Et pour conclure qu'un service répond, **lisez la réponse**. Le proxy de Docker
accepte une connexion avant que quoi que ce soit n'écoute : `nc -w 3 <cible>
80` doit afficher une ligne `jeton=`.

### Ce qui n'est pas noté

Le chemin. Recréer un conteneur, le rattacher puis le détacher, créer un
troisième réseau : tout ce qui aboutit à l'état demandé compte. Les contrôles ne
nomment aucun réseau.
