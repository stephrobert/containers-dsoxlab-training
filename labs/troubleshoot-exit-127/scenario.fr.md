# Le conteneur ne démarre pas, et les journaux sont vides

## La situation

Trois heures du matin, une sauvegarde n'a pas tourné. Le conteneur est arrêté.
Vous faites le geste réflexe, vous demandez ses journaux, et vous obtenez
**rien**. Pas une erreur, pas un avertissement : une sortie vide.

L'image a été construite hier, et la tentation est immédiate : c'est l'image. On
reconstruit, on relance, et ça échoue pareil. On passe une heure à chercher dans
le Dockerfile ce qui n'y est pas.

Un conteneur qui échoue laisse pourtant **toujours** un diagnostic. Il n'est
simplement pas là où on le cherche, et le code de sortie disait déjà où regarder.

## L'objectif

Se construire la grille. Trois conteneurs sont arrêtés, et les trois ont échoué
pour **trois raisons différentes** :

```text
panne-a   une commande qui n'existe pas
panne-b   un fichier qui existe mais n'est pas exécutable
panne-c   une commande qui s'exécute et échoue
```

Deux de leurs codes de sortie se ressemblent assez pour qu'on les confonde, et
le troisième n'a rien à voir.

Renseignez les trois lignes de `/opt/lab-exit/reponses.txt` :

```text
code_a=<le code de sortie de panne-a>
code_b=<le code de sortie de panne-b>
statut_a=<le STATUT de panne-a, tel que le moteur le déclare>
```

Puis **réparez** : lancez un conteneur nommé `repare`, **sur la même image**, qui
tourne.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## La troisième question est la plus utile

Regardez bien le statut de `panne-a`. **Ce n'est pas celui que vous attendez d'un
conteneur qui s'est arrêté**, et cela dit quelque chose d'important sur ce qui
s'est passé.

Regardez aussi les journaux des trois. L'un d'eux ne dit rien du tout, et son
diagnostic est ailleurs : dans l'inspection du conteneur, un champ que personne
ne lit jamais.

Ces deux observations expliquent l'une l'autre, et ensemble elles expliquent
l'heure perdue du scénario.

## Pourquoi la réparation se fait sur la même image

Parce que c'est la conclusion la plus rentable d'un dépannage : savoir ce qui
**n'est pas** responsable écarte la moitié des pistes.

Les trois pannes venaient de ce qu'on demandait au conteneur de lancer, pas de
ce que l'image contenait. Réparer en changeant d'image prouverait l'inverse de
la leçon, et le contrôle le refuse.

## Ce qui est noté

L'**état du système**. Les trois valeurs attendues sont lues sur les conteneurs
au moment de la notation, et aucune n'est écrite dans les contrôles : le jour où
ce lab changera de panne, ils suivront au lieu de devenir faux.
