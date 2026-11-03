# compose-sauver-et-restaurer : sauvegarder une stack, et le prouver

## Ce que ce lab apprend

Qu'une sauvegarde n'existe pas tant qu'on n'a pas restauré. Le travail ne
consiste pas à produire des archives, il consiste à remonter la stack ailleurs
et à montrer que les données servies sont les mêmes.

## Pourquoi ce lab existe

Il remplace `donnees-postgres-sauvegarde` auprès de la leçon C32, et pour une
raison de principe : **un lab n'exige que ce que la leçon enseigne**.

Le lab précédent demandait un PostgreSQL installé sur la VM, un
`sudo -u postgres`, un `CREATE DATABASE`, un `COMMENT ON DATABASE`, un
`pg_restore --no-owner --no-privileges` et un `scp` vers un second hôte. La
leçon C32 ne dit rien de tout cela : elle enseigne la sauvegarde et la
restauration **d'une stack Compose**. Un lab qui exige ce que la leçon n'a pas
introduit ne mesure plus l'apprentissage, il mesure la débrouille, et il recale
l'apprenant qui a pourtant suivi le cours.

Celui-ci ne demande rien qui ne soit dans la leçon : `pg_dump -Fc`, l'archivage
d'un volume par un conteneur et `tar`, l'archivage de la configuration, puis
`create`, les fichiers, `up -d --wait`, `pg_restore`.

## La stack est fournie, et c'est délibéré

L'apprenant reçoit une stack qui **marche** : une base PostgreSQL avec son
secret par fichier, et une vitrine qui sert un volume de planches. Lui demander
de l'écrire noterait le module précédent.

Il n'y a donc **aucune panne à trouver**, et c'est ce qui rend le lab difficile :
il y a une preuve à produire.

## Comment la restauration est prouvée, et pourquoi pas autrement

Par **empreinte**, et non par la présence d'un fichier de sauvegarde.

| ce qui est comparé | pourquoi ce n'est pas autre chose |
| --- | --- |
| `count` **et** `md5` du contenu agrégé, ordonné par identifiant | une table remplie de mauvaises valeurs a le bon nombre de lignes |
| `sha256sum` de chaque planche servie | un volume dont on recrée les fichiers à la main a le bon nombre de fichiers, pas les bons octets |

L'ordre dans l'agrégation n'est pas un détail : sans `order by`, deux bases
identiques rendraient deux empreintes différentes, et le contrôle refuserait du
travail juste.

Deux valeurs sont **tirées au sort à chaque passage**, l'une dans la base et
l'autre dans une planche. Elles n'existent nulle part ailleurs que dans la
source : une empreinte figée dans un dépôt public serait une réponse publiée.

## Les trois pièges posés, et ils sont dans la leçon

**Une copie à chaud du volume de base n'est pas une sauvegarde.** Elle semble
complète, elle porte un état intermédiaire, et elle se restaure sans erreur
jusqu'au jour où elle ne se restaure pas. Le contrôle ne regarde pas comment
l'archive a été faite, il regarde ce qu'elle **est** : `pg_restore --list` la
relit, ou elle n'est pas une sauvegarde logique.

**`docker compose exec` avale la suite d'un script.** Il lit son entrée
standard, donc les lignes qui suivent ne s'exécutent jamais. Le setup de ce lab
porte lui-même des `< /dev/null` pour cette raison : le piège mord l'auteur
comme l'apprenant.

**Restaurer sur une base remplie échoue.** `pg_restore` sort en erreur sur
`already exists`, et c'est une bonne nouvelle : il refuse d'écrire par-dessus.
C'est pour cela que la cible est **vierge**, et que l'ordre des gestes compte.

## Pourquoi `create` avant `up`

`docker compose create` crée les conteneurs **et leurs volumes** sans rien
démarrer. Cela donne un volume vide où verser les planches **avant** que la
vitrine le serve. Verser après `up -d` laisse un service qui a déjà monté un
volume vide.

## Le contrôle décisif

**Les données servies par la cible doivent égaler celles de la source.**

Une restauration qui rend des données fausses est pire qu'une restauration qui
échoue : un échec se voit et se reprend, des données fausses se découvrent le
jour où l'on en a besoin.

C'est le contrôle décisif, et non une exigence d'examen : **une exigence
bloquante n'existe que sur une épreuve**. `exam_blocking_checks` n'est accepté
que par un `lab_type` qui évalue, et ce lab est le TP d'une leçon. Ses cinq
contrôles valent donc chacun pour eux-mêmes.

## Ce que le lab ne mesure pas

Les commandes tapées. Le nom des archives. Le port de la cible. L'ordre exact
des gestes, dès lors que l'état final est juste.

Et il ne mesure pas non plus le transfert vers une autre machine : la leçon le
mentionne en une phrase sans l'enseigner, donc le lab ne le demande pas.

## Après le lab

`dsoxlab clean` retire les **deux** projets Compose, la source que le setup a
posée et la cible que l'apprenant a créée. Les images de la leçon restent : elles
viennent d'un registre public, elles servent aux autres labs Compose de la
machine, et les retirer coûterait un retéléchargement pour un objet que
l'apprenant n'a pas demandé.
