# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. **Trois conteneurs
sont arrêtés**, et les trois ont échoué pour trois raisons différentes :

```text
panne-a   une commande qui n'existe pas
panne-b   un fichier qui existe mais n'est pas exécutable
panne-c   une commande qui s'exécute et échoue
```

Deux de leurs codes de sortie se ressemblent assez pour qu'on les confonde, et
le troisième n'a rien à voir.

Les trois premières réponses vont dans `/opt/lab-exit/reponses.txt`, une ligne
par entrée, sans espace autour du signe égal.

## 1. Le code de sortie de `panne-a`

À la ligne `code_a=`.

Ce code ne dit rien du conteneur ni de l'image : il dit qu'une **commande** n'a
pas été trouvée. La nuance change tout le diagnostic, parce qu'elle oriente vers
le nom qu'on a écrit et non vers ce qu'on a construit.

## 2. Le code de sortie de `panne-b`

À la ligne `code_b=`.

Ici la commande **a été trouvée**, et elle n'a pourtant pas pu être exécutée.
Le code est un voisin du précédent, et c'est cette proximité qui les fait
confondre : l'un renvoie au nom de la commande, l'autre à ses permissions ou à
son format.

## 3. Le statut de `panne-a`

À la ligne `statut_a=`, tel que le moteur le déclare.

**Regardez-le bien.** Ce n'est pas le statut d'un conteneur qui s'est arrêté, et
cela dit quelque chose d'important sur ce qui s'est passé.

## Regardez aussi les journaux des trois

L'un d'eux ne dit **rien du tout**. Ce n'est pas une anomalie : c'est la
conséquence directe de la réponse à la question 3, et son diagnostic est
ailleurs, dans l'inspection du conteneur, un champ que personne ne lit jamais.

Cherchez-le. Il nomme la cause en une ligne, et c'est l'heure perdue du scénario
qu'il vous fera économiser.

## 4. Réparez, sur la même image

Lancez un conteneur nommé `repare`, **sur la même image** que les pannes, qui
**tourne**.

Le contrôle vérifie les deux : qu'il tourne, et qu'il dérive bien de la même
image. Réparer en changeant d'image prouverait l'inverse de la leçon.

Les trois pannes venaient de ce qu'on demandait au conteneur de lancer, pas de ce
que l'image contenait. **Savoir ce qui n'est pas responsable écarte la moitié des
pistes.**

## Ce qui n'est pas noté

La commande que vous avez tapée. Les codes se lisent de plusieurs façons, et la
réparation se fait avec n'importe quelle commande qui existe et qui dure.
