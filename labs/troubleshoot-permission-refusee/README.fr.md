# troubleshoot-permission-refusee : trois refus, trois causes

## Ce que ce lab éprouve

Que « problème de permissions » n'est pas un diagnostic. Trois conteneurs
butent sur un refus d'accès, et les trois causes n'ont aucun geste commun :

| Panne | Ce qui refuse | Ce qui la corrige |
| --- | --- | --- |
| le montage est en lecture seule | le **montage** | recréer le conteneur |
| les droits du répertoire ferment | les **droits** | aligner le groupe |
| le mode du fichier manque | le **mode**, venu de l'hôte | corriger sur l'hôte |

Le geste réflexe, un `chmod` large sur les trois répertoires, en règle **une
seule**. Les deux autres sont intactes, et le lab existe pour que cela se
mesure au lieu d'être affirmé.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Panne | Message du moteur | Inspection | Cause |
| --- | --- | --- | --- |
| A | « Read-only file system » | RW=**false** | le montage interdit |
| B | « Permission denied » | RW=**true** | les droits refusent |
| C | code **126** | RW=true | le mode du fichier manque |

**La leçon est dans la paire A/B.** Les deux messages sont déjà différents, et
on les lit souvent comme un seul. Le premier accuse le montage ; le second dit
que le montage est d'accord et que ce sont les droits qui refusent.
L'inspection les sépare en un mot, et c'est ce mot que le premier contrôle
demande.

## Pourquoi le C relie ce lab au précédent

Son code est celui du fichier **trouvé mais non exécutable**, déjà rencontré
dans `troubleshoot-exit-127`. Même code, autre cause : ici le fichier vient
d'un montage, et **un montage ne change aucun mode**. Celui du fichier est
celui de l'hôte, et il le restera.

C'est pourquoi un `chmod` joué dans le conteneur ne sert à rien, et pourquoi le
conteneur ne démarre de toute façon pas assez longtemps pour qu'on y joue quoi
que ce soit.

## Le seul contrôle du catalogue qui refuse une solution qui marche

Repasser `perm-b` en root règle son symptôme en une option, et le quatrième
contrôle l'interdit.

Ce n'est pas une coquetterie. `donnees-permissions-uid-gid` a déjà montré la
bonne réponse, qui est d'aligner le groupe avec le bit setgid. Un lab de
dépannage qui accepterait le raccourci défairait ce qu'un lab de méthode a
enseigné, et c'est exactement ce qu'un apprenant retient : le geste qui a fait
passer le contrôle.

## Pourquoi un témoin, et pourquoi on interdit de le réparer

La troisième réponse est un **code de sortie**, et un conteneur réparé n'en
porte plus : il tourne.

`temoin-sans-bit` monte le même répertoire et échoue de la même façon. Le code
se lit sur lui, l'énoncé interdit de le réparer, et un contrôle vérifie qu'il
est resté en panne. Sans cette dernière vérification, le réparer rendrait la
question sans objet, et le lab noterait une valeur qui n'existe plus.

C'est la troisième fois que cette parade sert dans la section. La règle qui en
sort : **une valeur de diagnostic ne se lit jamais sur l'objet que la
réparation modifie.**

## Chaque réparation est éprouvée par l'effet

Une écriture réelle pour les deux premières, la trace du script pour la
troisième. Jamais une option de ligne de commande, qui ne dirait que ce qui a
été tapé.

Les trois valeurs attendues, elles, sont lues sur les conteneurs au moment de
la notation : aucune n'est écrite dans les contrôles.

## L'état de départ est cassé, et c'est la règle du dépôt

Les quatre contrôles sont faux avant tout travail. Une tâche du setup
**vérifie** que le montage de `perm-a` est bien en lecture seule, que `perm-b`
ne peut pas écrire, et que ni `perm-c` ni le témoin ne tournent : sans elle, un
passage mal nettoyé rendrait le lab déjà résolu.

## Un piège du cleanup, payé d'avance

Le répertoire de l'atelier part **en entier**. Les trois pannes vivent dans ses
droits et dans le mode d'un fichier : s'il survivait réparé, les trois
contrôles de réparation seraient vrais au passage suivant. Le recréer coûte
moins cher que de remettre chaque droit en place, et surtout cela ne peut pas
en oublier un.

## Ce que le lab n'exige pas

Un chemin. Les trois valeurs se trouvent de plusieurs façons, et les trois
réparations se font par n'importe quel moyen qui produise l'effet attendu, root
excepté pour la deuxième.
