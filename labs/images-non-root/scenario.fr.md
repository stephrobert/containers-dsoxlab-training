# Ajouter `USER` casse l'application

## La situation

Un audit demande que les conteneurs ne tournent plus en root. Le geste tient en
une ligne : ajouter un `USER` au Dockerfile.

On le fait, on reconstruit, et l'application **cesse d'écrire**. Le message
parle de permission refusée sur un répertoire que le Dockerfile vient de créer
deux lignes plus haut.

Le réflexe est alors de revenir en arrière, ou d'ouvrir le répertoire à tout le
monde. Les deux font repartir l'application, et les deux ratent l'audit.

## L'objectif

Le contexte est dans `/opt/lab-nonroot/appli`. Construisez le Dockerfile tel
quel : l'application tourne, écrit son journal, et elle est root.

Ajoutez un `USER`, reconstruisez, et lisez le message.

Construisez `appli:nonroot`, qui doit :

```text
imprimer son jeton, tourner sous un uid NON NUL par défaut, et ÉCRIRE
avoir un répertoire de données qui lui APPARTIENT, et qui n'est pas
  ouvert à tout le monde
déclarer son utilisateur par un UID NUMÉRIQUE
```

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Pourquoi `USER` seul ne suffit jamais

`USER` change l'identité d'exécution. Il ne change **aucun droit**.

Les répertoires créés avant lui appartiennent à root, et un processus non-root
n'y écrit plus. Mesuré sur cette machine : `can't create
/donnees/journal.txt: Permission denied`.

La réponse est d'aligner le **propriétaire** sur l'utilisateur de
l'application. Pas d'ouvrir le répertoire : un répertoire inscriptible par
n'importe qui défait exactement ce que le passage en non-root cherchait, et un
contrôle le refuse.

## Pourquoi l'uid doit être numérique

Un `USER appli` se résout dans le `/etc/passwd` **de l'image**.

Un orchestrateur qui refuse les conteneurs root ne lit pas ce fichier : il lit
la déclaration de l'image, et il ne peut pas prouver qu'un nom n'est pas root.
Un uid numérique se vérifie sans rien ouvrir.

## Deux mesures qui contredisent ce qu'on croit

**`docker run --user 0:0` sur l'image non-root rend uid=0.** Le `USER` du
Dockerfile est une valeur par défaut, pas une garantie : qui lance décide. C'est
pourquoi les contrôles lancent l'image **sans aucune option d'identité** : ils
mesurent ce qu'elle fait quand personne ne décide à sa place.

**Un non-root écoute sur le port 80** dans un conteneur, mesuré. On lit souvent
qu'il faut être root pour les ports sous 1024 ; le moteur accorde la capacité
par défaut, et l'argument tombe. Aucun contrôle ne porte donc sur les ports : ce
serait mesurer une croyance.

## Ce qui est noté

L'**état du système**, et le **moyen** autant que l'effet. Le deuxième contrôle
vérifie que l'application écrit ; le troisième, qu'elle y arrive parce que le
répertoire est à elle, et non parce qu'il est ouvert à tous.

C'est la même structure que `troubleshoot-permission-refusee`, où repasser en
root est refusé bien que cela marche.
