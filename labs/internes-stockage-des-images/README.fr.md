# internes-stockage-des-images : où atterrissent les fichiers

## Ce que ce lab éprouve

Que ce qu'un conteneur écrit n'est **pas nulle part** : c'est sur le disque de
l'hôte, dans un répertoire ordinaire qu'on peut ouvrir.

Les deux labs précédents montraient ce qu'un conteneur voit et ce qu'il peut
consommer. Celui-ci clôt le triptyque des internes : où ses fichiers
atterrissent.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Fait | Valeur |
| --- | --- |
| pilote de stockage | `overlay2`, racine `/var/lib/docker` |
| couche d'écriture d'un conteneur | `GraphDriver.Data.UpperDir` |
| fichier écrit dans le conteneur | lisible **immédiatement** à ce chemin, depuis l'hôte |
| contenu de la couche après une écriture | ce fichier **seul**, rien d'autre |

C'est le dernier point qui rend la notion claire : la couche d'écriture ne
contient pas une copie du système de fichiers, elle ne contient que les
**différences**. C'est ce qui rend les conteneurs légers, et ce qui fait qu'ils
grossissent sans qu'on les voie grossir.

## Un piège évité à l'écriture du lab

Pour démontrer qu'une écriture atterrit dans la couche, la première idée était
de faire modifier `/etc/hostname`.

**Mesuré : la modification n'apparaît pas dans la couche.** Ce fichier est un
montage que Docker pose depuis le répertoire du conteneur, et non un fichier de
l'image. Un contrôle fondé dessus aurait échoué quoi que fasse l'apprenant.

Les contrôles portent donc sur des fichiers créés **à la racine**, qui n'ont pas
ce statut particulier.

## Pourquoi la quatrième mesure est une pesée

Parce que c'est la conséquence qui compte en exploitation. La couche d'écriture
n'est pas gratuite, et elle explique le lab `troubleshoot-disque-plein` de cette
même section, où une machine se remplit sans qu'aucun volume soit en cause.

La taille est mesurée **sur l'hôte**, dans la couche, et non dans le conteneur :
c'est le disque de la machine qui se remplit, pas un espace à part.

## Un détail qui a changé la solution de référence

La charge est écrite avec de **vrais octets**, et non allouée. Un fichier alloué
sans être écrit peut n'occuper aucun bloc sur le disque, et la pesée le
compterait pour zéro.

C'est le genre de détail qui fait passer un lab pour cassé alors que c'est la
mesure qui était fausse.

## La correction de quoting qui vaut d'être retenue

La première version du setup lisait la couche avec
`index .GraphDriver.Data "UpperDir"`. Les guillemets, échappés pour traverser
YAML, arrivaient littéralement à Go, qui refusait avec
« unexpected `\\` in operand ».

**La forme pointée `.GraphDriver.Data.UpperDir` fait la même chose sans un seul
guillemet**, parce que Go accepte l'accès par point sur une map dont la clé est
un identifiant valide. Vérifié sur la machine, puis appliqué au setup, aux tests
et à la solution.

## Le préalable qui évite d'accuser l'apprenant

Un moteur réglé sur un autre pilote ne porte pas `UpperDir`, et deux contrôles
échoueraient en parlant de couches. Le setup et les tests vérifient donc le
pilote avant toute mesure, et le disent.

## L'élévation est indispensable ici

`/var/lib/docker` n'est pas lisible par un compte ordinaire. Le premier essai de
conception de ce lab s'y est fait prendre : un test de lisibilité jouait sans
élévation et rendait un faux négatif, ce qui a failli faire conclure que le
pilote n'exposait pas de couche.

## L'état de départ est cassé, et c'est la règle du dépôt

Le conteneur est **vierge** : aucune écriture dedans, donc sa couche est vide.
Une tâche du setup le vérifie, ce qui garantit que les deux écritures de
l'apprenant s'y voient.

## Ce que le cleanup doit retirer, et ce qu'il n'a pas à retirer

Retirer le conteneur suffit, et **c'est la démonstration du lab** : sa couche
d'écriture part avec lui, et les mégaoctets avec elle.

Les couches de l'**image**, en revanche, survivent à l'image jusqu'au `prune` :
c'est pour cela qu'il figure dans le cleanup, et ce n'est pas décoratif.

## Ce que le lab n'exige pas

Un chemin. Les deux valeurs se lisent par l'inspection comme dans la sortie
générale du moteur, et les deux écritures se font depuis le conteneur par
n'importe quel moyen. Seul l'état compte.
