# container-ulimits-et-shm : deux réglages qu'on ne regarde jamais

## Ce que ce lab éprouve

Que deux réglages qu'on ne regarde jamais décident du sort d'un conteneur, et
qu'ils ne sont **pas de la même famille**.

Les cgroups plafonnent depuis l'extérieur ; les ulimits sont un mécanisme POSIX,
bien antérieur, que le processus porte lui-même. Les chercher au même endroit est
l'erreur que ce lab lève.

Il clôt la famille des limites, après `container-limite-cpu`.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Fait | Valeur |
| --- | --- |
| `/dev/shm` par défaut | **64 Mo**, et c'est un tmpfs |
| `ulimit -n` par défaut | **1073741816** |
| `--shm-size 64m` | `.HostConfig.ShmSize` = 67108864 |
| `--ulimit nofile=256:256` | `ulimit -n` = 256 **dans** le conteneur |
| 64 Mo écrits dans `/dev/shm` | `memory.current` du cgroup à 67616768 |

## La deuxième valeur surprend, et c'est pour cela qu'elle est demandée

La limite de descripteurs **n'est pas** le problème des conteneurs modernes :
elle est énorme par défaut. C'est son **réglage à la baisse** qui en crée un.

Un apprenant qui lit ce nombre et croit s'être trompé a appris quelque chose de
plus utile qu'une valeur : il saura reconnaître un réglage hérité d'un autre
temps, et il ne cherchera pas une pénurie là où il n'y en a pas.

## La leçon majeure est le quatrième contrôle

`/dev/shm` est un tmpfs, donc de la **mémoire**, et cette mémoire est comptée
dans le cgroup du conteneur. Écrire 128 Mo dedans fait monter `memory.current`
d'autant.

Conséquence : **une limite mémoire doit tenir compte de la taille de
`/dev/shm`**, sans quoi le conteneur se fait tuer pour une mémoire qu'il croyait
« à part ». C'est l'incident du scénario, et c'est une cause de mort qui ne se
lit dans aucune documentation d'application.

Le contrôle pèse les deux côtés et compare : l'occupation du système de fichiers,
et la mémoire du cgroup.

## Aucune valeur par défaut n'est écrite en dur

Les deux premières réponses sont **remesurées** au moment de la notation, sur un
conteneur neuf lancé sans aucune option.

Écrire `64` et `1073741816` dans les tests marcherait aujourd'hui et mentirait
le jour où Docker changera ses défauts : les contrôles passeraient au rouge sans
qu'aucun lab ne soit cassé. La solution de référence applique la même règle.

## Un seul conteneur jetable répond aux deux questions

Les deux valeurs se lisent dans le même shell. Deux conteneurs auraient été deux
fois plus lents pour le même résultat, et c'est le genre de détail qui compte
quand un cycle de validation enchaîne trois passages.

## De vrais octets, et c'est mesuré

L'écriture dans `/dev/shm` emploie `dd`. Un fichier **alloué** sans être écrit
n'occuperait aucune page, et ni l'occupation du système de fichiers ni la mémoire
du cgroup ne monteraient.

C'est la même leçon que dans `internes-stockage-des-images`, et elle se paye au
même endroit : une pesée ne mesure que ce qui a vraiment été écrit.

## Une faute de YAML évitée de peu, et elle méritait son commentaire

La vérification finale du setup devait refuser un conteneur déjà présent. Écrite
`cmd: ! docker container inspect …`, elle a été **avalée par le parseur** : en
YAML, un `!` en tête de scalaire est un indicateur de **tag**.

Mesuré le 2026-10-30 : la commande devenait `docker container inspect etroit …`,
c'est-à-dire l'inverse exact du contrôle voulu, et le setup aurait exigé que le
conteneur existe déjà.

Le reste du catalogue n'est pas touché : les autres négations vivent dans des
scalaires **repliés**, où le `!` n'est plus en tête. Les treize vérifications
concernées ont été relues une à une après coup.

## Deux préalables qui évitent d'accuser l'apprenant

La machine doit être en cgroup v2, et elle doit avoir assez de **mémoire libre**
pour l'épreuve : le quatrième contrôle demande d'écrire 128 Mo en mémoire, en
plus de ce que la machine porte déjà.

Le setup vérifie les deux avant de poser le lab.

## L'état de départ est cassé, et c'est la règle du dépôt

Aucun conteneur ne tourne, et le formulaire est vide. C'est le setup le plus
léger du catalogue, et c'est volontaire : les deux réglages du lab ne se posent
qu'à la création, et il n'y a rien à observer sur un conteneur déjà réglé.

## Ce que le cleanup doit retirer, et ce qu'il n'a pas à retirer

Le conteneur, et **c'est la démonstration du lab** : son `/dev/shm` est de la
mémoire, et cette mémoire part avec lui. Aucun fichier ne subsiste sur le disque,
contrairement à un volume, et c'est exactement ce que le quatrième contrôle a
fait constater.

## Ce que le lab n'exige pas

Un chemin. Les deux réglages se posent en ligne de commande comme par l'API, et
l'écriture dans la mémoire partagée par n'importe quel outil qui écrit de vrais
octets.
