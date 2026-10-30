# Tout le monde parle à tout le monde

## La situation

Vous reprenez un serveur qui héberge une douzaine de conteneurs : deux
applications métier, leurs bases, un service de métrologie, et trois outils
qu'un ancien collègue avait installés « pour tester ».

Aucun n'a reçu d'option réseau. Ils sont donc tous sur le réseau par défaut, et
cela a deux conséquences que vous découvrez le même jour.

La première, agaçante : les applications doivent se parler par adresse IP,
parce que les noms ne résolvent pas. Les adresses sont écrites dans les
configurations, et elles changent au moindre redémarrage.

La seconde, nettement plus sérieuse : **les trois outils de test joignent les
bases de production**. Personne ne l'a voulu, personne ne l'a interdit. Sur un
réseau partagé, tout le monde parle à tout le monde.

## L'objectif

Donner un réseau à l'application, et constater que cela règle les deux
problèmes à la fois. Trois conteneurs tournent, **tous** sur le réseau par
défaut :

```text
arriere   il ÉCOUTE sur le port 8080 et répond un jeton
avant     il doit pouvoir joindre `arriere` PAR SON NOM
tiers     le témoin : il ne doit PLUS pouvoir joindre `arriere`
```

Quatre choses sont attendues :

1. Un réseau nommé `atelier` existe, avec le sous-réseau **172.28.5.0/24**.
2. `avant` et `arriere` y sont attachés, et ils ne sont **plus** sur le réseau
   par défaut.
3. Depuis `avant`, le **nom** `arriere` se résout et rend son adresse sur
   `atelier`.
4. `tiers`, laissé sur le réseau par défaut, **ne joint plus** `arriere`.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Le piège, et il est fréquent en vrai

**Attacher un conteneur à un réseau ne le retire pas de l'autre.** Un conteneur
peut être sur deux réseaux à la fois, et il garde alors toute sa joignabilité
depuis le réseau par défaut.

C'est la faute qui fait croire à une isolation qui n'existe pas : le nom résout,
l'application fonctionne, tout semble en ordre, et les outils de test joignent
toujours la base. Le deuxième contrôle exige donc les **deux** gestes.

## Ne touchez pas à `tiers`

C'est le témoin. Le détruire ou le déplacer ferait passer le quatrième contrôle
sans rien prouver, et les contrôles vérifient nommément qu'il est toujours là,
sur le réseau par défaut et lui seul.

Ce qui doit changer, c'est le réseau de `arriere`, pas celui du témoin.

## Ce qui est noté

L'**état du moteur**, et rien d'autre. Il n'y a aucun formulaire dans ce lab :
un réseau existe ou non, un conteneur en est membre ou non, un nom se résout ou
non, une connexion aboutit ou non.

Un détail qui a sa valeur : le troisième contrôle ne se contente pas d'une
résolution qui aboutit, il vérifie aussi que la connexion passe. **Résoudre
n'est pas joindre** : un résolveur peut très bien répondre pour une adresse
qu'aucune route n'atteint.
