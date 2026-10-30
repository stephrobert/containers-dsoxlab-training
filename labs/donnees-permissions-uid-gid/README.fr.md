# donnees-permissions-uid-gid : des droits qui tiennent

## Ce que ce lab éprouve

Qu'un volume monté appartient à root, qu'un conteneur non-root n'y écrit donc
pas, et que la réponse n'est **ni** de passer le conteneur en root, **ni**
d'ouvrir le volume à tout le monde. C'est le groupe qu'on aligne.

Les deux mauvaises réponses sont l'état de départ du lab, et ce n'est pas une
caricature : ce sont celles qu'on trouve en production, dans cet ordre, avec
six mois d'écart.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| État | propriétaire du volume | uid 1000 écrit | uid 1001 écrit |
| --- | --- | --- | --- |
| volume frais | `0:0`, mode `755` | non | non |
| après `chown root:2000` et `chmod 2775` | `0:2000`, mode `2775` | oui | oui |

Et le détail qui fait la différence entre une solution qui tient et une qui
marche une fois : avec le **bit setgid**, les fichiers créés portent le groupe
`2000`. Sans lui, chacun porterait le groupe primaire de son auteur, et le
voisin ne pourrait pas le reprendre.

## Pourquoi deux conteneurs, et non un

Parce qu'avec un seul, `chown 1000` suffirait, et le lab enseignerait la
mauvaise leçon. Deux conteneurs d'**uid différents** rendent la question
intéressante : aucun propriétaire ne convient aux deux, et seul un groupe
partagé y répond.

C'est la situation réelle dès qu'une application et son outil de sauvegarde se
partagent des données, et c'est elle qui justifie la technique.

## Le quatrième contrôle écarte la fausse solution

`chmod 777` ferait passer les trois premiers contrôles : les deux conteneurs
écriraient, et les fichiers seraient bien à eux.

Il refuse donc explicitement un volume ouvert en écriture aux **autres**, parce
que c'est la réponse qu'on trouve partout et qu'elle donne à n'importe quel
processus du conteneur le droit de tout réécrire. Le groupe partagé suffit, et
il **nomme** qui peut écrire.

Les deux moitiés de ce contrôle sont indissociables : l'autre uid doit écrire,
et le volume ne doit pas être ouvert à tous. Séparées, chacune se satisferait
d'une solution que l'autre refuse.

## L'identité est lue dans le conteneur, pas dans ce qui a été demandé

Les contrôles lisent `id -u` et `id -g` **à l'intérieur** du conteneur, et non
`.Config.User`.

Un `--user` peut désigner un compte que l'image ne connaît pas : le conteneur
démarre, mais le compte n'a ni nom ni répertoire personnel, et les messages
deviennent incompréhensibles. C'est l'identité réelle des processus qui décide
des droits, pas ce qui a été écrit à la création.

## Les contrôles écrivent pour mesurer

Lire les permissions ne suffit pas : c'est la capacité d'écrire qui est le
sujet, et une permission se déclare sans toujours produire l'effet attendu.

Chaque contrôle fait donc écrire le conteneur, lit le propriétaire du fichier
obtenu, puis **retire le fichier**. Un contrôle qui laisserait sa trace dans le
volume polluerait le rejeu, que le cycle de validation joue trois fois.

## Pourquoi l'image porte les deux comptes

Un `--user 1001:2000` fonctionne sur une image qui ne connaît pas ce compte,
mais le shell n'a alors ni nom ni répertoire personnel. L'image déclare donc
`redacteur` et `verificateur`, tous deux dans `equipe` : c'est ce qui rend les
messages d'erreur lisibles et le lab enseignable.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu |
| --- | --- | --- |
| `rapport` | tourne en **root** | le recréer sous son compte |
| `verificateur` | non-root, n'écrit rien | rien : c'est le témoin |
| le volume | `0:0`, mode `755` | le donner au groupe, avec le setgid |

Une tâche du setup **vérifie** cet état avant de rendre la main : `rapport` est
bien en root, le volume appartient bien à root, et `verificateur` ne peut rien
y écrire.

## Ce que le cleanup doit impérativement retirer

Le **volume**. Ses permissions sont ce que le lab fait corriger : s'il
survivait corrigé, trois contrôles sur quatre seraient vrais au passage suivant
avant tout travail. Un volume recréé repart de `0:0` et `755`, mesuré, et c'est
l'état de départ du lab.

## Ce que le lab n'exige pas

Un chemin. Les droits du volume se changent par un conteneur jetable comme
depuis l'hôte, et le conteneur se recrée en ligne de commande comme par l'API.
Seul l'état compte, et il est mesuré par l'écriture.
