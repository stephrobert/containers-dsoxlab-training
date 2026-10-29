# Écrire les labs : état du chantier et contrat d'écriture

Établi le **2026-10-29**, quand les squelettes des 70 labs du backlog ont été
créés et rangés. Ce fichier dit ce qui est déjà fait, ce qui reste à faire lab
par lab, et les règles qu'un lab doit tenir pour être attesté.

Le backlog lui-même, avec le `doc_url` ancré de chaque lab et la justification
de son découpage, vit dans `ROADMAP.md`. Ce fichier-ci ne le répète pas : il
décrit le **geste d'écriture**.

## Ce qui est déjà fait, et qu'il ne faut pas refaire

| Fait | État |
|---|---|
| Squelettes créés par `dsoxlab new lab … --runtime vm` | **70**, plus `images-identifier-image` déjà écrit |
| Rangement dans les neuf sections de `meta.yml` | fait, `validate-structure` rend « Tous les labs sont valides » |
| `level` (`c1` à `c4`), `doc_url` ancré, `lab_type` | **pré-remplis** depuis le backlog, dans `lab.yaml` et `lab.fr.yaml` |
| Hôte des cibles | aligné sur `docker.lab`, le seul hôte que `meta.yml` déclare |

Les squelettes sortent de `dsoxlab new lab`, **jamais** d'une copie d'un lab
voisin ni d'un `lab.yaml` écrit à la main : une copie emporte les écarts du
voisin, un fichier écrit à la main dérive du contrat. Un lab qui s'ajouterait
plus tard se crée de la même façon.

Deux pièges déjà payés sur ce catalogue, pour qu'ils ne reviennent pas :

- `dsoxlab new lab` **ne range pas** le lab dans une section. Il prévient que
  le lab « n'a aucune place dans la progression » ; sur d'autres catalogues, il
  l'inscrit dans la **première** section, et dix-neuf labs GitLab s'y étaient
  empilés pendant que trois sections restaient vides ;
- l'entrée d'une section s'écrit **sans** le préfixe `labs/`. Avec lui, le
  validateur cherche `labs/labs/<id>` et refuse le catalogue entier.

## Ce qui reste à écrire, lab par lab

Dans `labs/<id>/` :

    lab.yaml  /  lab.fr.yaml   title, description, skills, distros, validation
    scenario.md  /  .fr.md     l'énoncé que l'apprenant lit
    setup.yaml                 l'état de départ, posé par Ansible
    cleanup.yaml               ce qui défait le setup
    challenge/tests/           les assertions qui notent

Les champs encore marqués « À remplir » ou `a-remplir` sont exactement ceux qui
restent. `skills` et `distros` sont REQUIS et non vides : un lab sans eux est
refusé, ou disparaît du catalogue sans un mot.

## Les règles qui décident si un lab est bon

### Un test doit porter sur ce que l'état de départ ne porte PAS

C'est la règle la plus souvent enfreinte, et elle a coûté quatre rejeux rouges
sur le catalogue GitLab CI. `valider-labs.py` exige un score **nul** sur l'état
de départ : un test vert avant tout travail n'est pas un test, c'est une
hypothèse du setup.

Quand une exigence est déjà vraie au départ (le service tourne, un fichier
existe), elle ne devient pas un test à elle seule : elle s'ajoute au test qui
mesure le travail réel. Et un motif cherché dans un journal doit être propre au
succès, jamais une chaîne qui apparaît aussi dans l'échec.

### La note porte sur l'état du système, jamais sur les commandes tapées

Une image qui a été construite, sa taille, l'utilisateur qui exécute le
conteneur, les montages, ce que l'application répond. Relire un fichier noterait
l'intention ; interroger le moteur note le résultat.

### Un lab se joue dans les deux sens avant d'être attesté

    python3 scripts/valider-labs.py --lab <id>

Il rejoue `clean`, `run`, `check` (attendu 0), applique la solution de
référence, `check` (attendu 100), puis `clean`. Le verdict va dans
`validation-labs.json`. Un lab sans ce cycle n'est pas livré, quel que soit son
contenu.

### Rien ne se teste sur le poste de travail

Tout tourne sur la VM `docker.lab` (Debian 13, réseau `lab-containers`,
10.10.120.0/24), déclarée dans `meta.yml`. C'est une décision éditoriale autant
que technique : on n'impose pas Docker sur la machine de l'apprenant.

### Les références s'épinglent, même dans un exemple

Toute image porte la forme `image:tag@sha256:…`. Jamais `:latest`, jamais un
tag seul. Un contre-exemple volontaire porte un marqueur explicite, pour que
les outils d'épinglage ne le « corrigent » pas et ne détruisent pas la
démonstration.

## L'ordre d'écriture

Celui du parcours, et il est déjà justifié dans `ROADMAP.md` :

    1  conteneurs-utilisation      14 labs
    2  images-construction          8 labs restants
    3  conteneurs-isolation        10 labs
    4  images-distribution          6 labs
    5  compose-application          9 labs
    6  compose-exploitation         2 labs
    7  docker-administration       17 labs
    8  docker-industrialisation     3 labs

Deux sections passent devant leur rang si l'on veut corriger un déséquilibre
réel : `compose-exploitation` et `docker-industrialisation` n'ont que cinq labs
à eux deux, pour quatre leçons annoncées chacun. Le backlog a grandi là où les
guides publiés étaient les plus denses, pas là où la formation promet le plus.

## Ce que le catalogue ne décide pas

Un lab ne devient visible pour un lecteur que lorsqu'une page du site pose son
bloc `<Lab>`. Aucune page ne cite encore ce catalogue : le câblage est un
travail du dépôt du site, et il suit la livraison, il ne la précède pas.

Le dépôt se commite **en local**. La livraison est un geste humain.
