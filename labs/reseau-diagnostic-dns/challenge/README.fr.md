# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service.

```text
boutique    l'application. Elle cherche sa base sous le nom `base`, en dur
            dans sa configuration, et ce nom ne peut pas changer.

catalogue   la base. Elle écoute sur son port 80 et répond un jeton.
```

Les deux tournent, les deux répondent quand on les interroge de l'intérieur, et
l'application ne joint rien. L'audit signale par ailleurs que la base est
joignable depuis l'extérieur.

## Les quatre contrôles

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

## C'est une épreuve

**Rien ne vous sera réexpliqué.** Les cinq labs réseau du parcours ont enseigné
ce qu'il faut savoir. Celle-ci mesure.

Quatre contrôles de poids égal, **75 points pour réussir**. Les messages des
contrôles nomment le symptôme, jamais le geste : faire le lien est le travail.

Quatre indices existent, du plus vague au plus explicite, et ils coûtent des
points. Le dernier nomme les fautes qui laissent croire au succès.

## Deux choses qui ne sont pas des indices

Gardez les **noms** des conteneurs : les contrôles les cherchent nommément, et
le quatrième point vous dit déjà pourquoi.

Et pour conclure qu'un service répond, **lisez la réponse**. Le proxy de Docker
accepte une connexion avant que quoi que ce soit n'écoute : `nc -w 3 <cible>
80` doit afficher une ligne `jeton=`.

## Ce qui n'est pas noté

Le chemin. Recréer un conteneur, le rattacher puis le détacher, créer un
troisième réseau : tout ce qui aboutit à l'état demandé compte. Les contrôles ne
nomment aucun réseau.
