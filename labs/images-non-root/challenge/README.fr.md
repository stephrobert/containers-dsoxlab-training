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

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le contexte est dans
`/opt/lab-nonroot/appli` :

```text
Dockerfile   il MARCHE, et l'application tourne en root
lancer.sh    elle dit son identité, et elle ÉCRIT un journal
```

**Commencez par construire tel quel**, puis ajoutez un `USER` et reconstruisez.
L'identité change, et l'application cesse d'écrire. Lisez le message.

### 1. L'image doit tourner sous un uid non nul par défaut

`appli:nonroot` doit imprimer son jeton et tourner sous un uid **non nul**, sans
qu'aucune option ne soit passée au lancement.

Le contrôle ne pose pas `--user`, et c'est la seule façon de mesurer ce que
l'image décide. Mesuré sur cette machine : `--user 0:0` rend uid=0 **sur
l'image non-root elle-même**. Le `USER` du Dockerfile est une valeur par
défaut, pas une garantie.

### 2. L'application doit continuer d'écrire son journal

C'est le piège, et il tombe sur tout le monde une fois.

`USER` change l'identité et **aucun droit**. Le répertoire créé avant lui
appartient à root, et un processus non-root n'y écrit plus. Le contrôle mesure
une écriture réelle, pas la présence d'une instruction.

### 3. Le répertoire doit lui appartenir, sans être ouvert à tous

Deux réponses font écrire l'application : lui **donner** le répertoire, ou
l'**ouvrir** à tout le monde. La seconde marche, et elle est refusée ici.

Rendre un répertoire inscriptible par n'importe qui pour qu'un processus non
privilégié y écrive défait exactement ce que le passage en non-root cherchait à
obtenir. C'est la même structure que `troubleshoot-permission-refusee`, où
repasser en root est refusé bien que cela marche.

### 4. L'utilisateur doit être déclaré par un uid numérique

Un `USER appli` se résout dans le `/etc/passwd` de l'image.

Un orchestrateur qui refuse les conteneurs root ne lit pas ce fichier : il lit
la déclaration de l'image, et il ne peut pas prouver qu'un nom n'est pas root.
Un uid numérique se vérifie sans rien ouvrir.

Le contrôle accepte `10001` comme `10001:10001`, et refuse `appli`.

### Une croyance que ce lab ne note pas

**Un non-root écoute sur le port 80** dans un conteneur, mesuré sur cette
machine. On lit souvent qu'il faut être root sous 1024, et l'explication
habituelle est fausse : ce n'est pas une capacité. Les capacités effectives d'un
processus lancé en `--user 10001:10001` sont **nulles**, et il écoute encore sous
`--cap-drop ALL`. Le moteur abaisse le seuil lui-même, dans l'espace de noms
réseau du conteneur : `net.ipv4.ip_unprivileged_port_start` y vaut `0`. Remontez-le
à `1024` et le même conteneur répond `nc: bind: Permission denied`.

La nuance compte : qui croit à une capacité cherchera `--cap-add NET_BIND_SERVICE`
pour un problème que ce drapeau ne résout pas. Aucun contrôle ne porte donc sur
les ports : ce serait mesurer une croyance plutôt qu'un état.

### Ce qui n'est pas noté

La commande que vous avez tapée, ni l'uid choisi, ni le nom de l'utilisateur.
Seul compte que l'uid ne soit pas nul, que le répertoire soit à lui, et que la
déclaration soit numérique.

Attention à l'ordre, en revanche : toute instruction placée après le `USER`
tournera sous cette identité, et ne pourra plus ni créer ni donner.
