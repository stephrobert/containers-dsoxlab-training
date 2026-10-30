# images-contexte-de-build : un fichier qui existe, et qu'on ne trouve pas

## Ce que ce lab éprouve

Qu'un `COPY` ne peut pas sortir du contexte de construction, et que **le message
ne le dit plus**. Le fichier existe, le moteur dit qu'il est introuvable, et
l'heure perdue à chercher une faute de frappe est le coût de cette phrase.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30, le même Dockerfile sous les deux constructeurs :

| Constructeur | Message |
| --- | --- |
| buildkit, le défaut | `"/commun/version.txt": not found` |
| classique, `DOCKER_BUILDKIT=0` | `forbidden path outside the build context` |

Le second nommait la cause. Le premier dit « introuvable », parce que le `..`
est normalisé puis écrasé : le moteur ne regarde que dans le contexte, et rend
compte de ce qu'il voit, pas de ce qui est. **Le message s'est dégradé en
changeant de constructeur**, et c'est pourquoi tant de réponses trouvées en
ligne parlent d'un fichier manquant.

Et la réponse paresseuse a été **éprouvée** : recopier le fichier partagé dans
le répertoire de l'application rend **3/4**, le quatrième contrôle refusant
seul. Si elle avait donné 4/4, la contrainte du lab n'aurait été qu'une phrase
dans un énoncé.

## Une mesure qui a changé le lab que j'allais écrire

Le premier design notait le **poids du contexte** : un gros répertoire dans le
dépôt, et l'exclusion pour alléger le transfert. La mesure l'a démonté.

Sous buildkit, avec 20 Mo d'archives dans le dépôt, `transferring context`
annonce **2 octets**, et l'image pèse **exactement** la taille du socle, avec et
sans exclusion. Buildkit n'envoie que ce dont les `COPY` ont besoin.

Noter le temps de transfert aurait donc mesuré une croyance, et le lab aurait
enseigné un argument devenu faux. Ce qui reste vrai est ailleurs : élargir le
contexte met tout le dépôt à portée d'un `COPY .`, secret compris.

## Pourquoi un script de construction

Les trois autres contrôles le **rejouent**, et c'est la seule façon de vérifier
que le fichier partagé est toujours la source unique : sans script, la commande
de construction n'existe nulle part, et on ne pourrait que relire le Dockerfile,
ce qui noterait la forme.

Le contrôle le joue dans une **copie** du dépôt, d'où l'exigence de chemins
relatifs. Un chemin absolu repointerait sur le dépôt d'origine, et construirait
autre chose que ce qu'on mesure.

## Pourquoi l'étiquette de l'apprenant est sauvegardée

Le script reconstruit sous le nom attendu : le jouer dans une copie **écrase**
l'image de l'apprenant.

Sans parade, le `check` suivant trouverait une image portant la version du
contrôle, et le deuxième contrôle refuserait un travail correct. L'étiquette est
donc mise de côté avant, et rendue après. Vérifié après coup : l'image porte
toujours sa version d'origine, et aucune étiquette de sauvegarde ne subsiste.

**Un test ne laisse pas le système dans un état qu'il a produit**, et c'est la
règle qui gouverne aussi les reconstructions en bac d'essai de
`images-ordre-des-couches`.

## Pourquoi le secret est cherché par son contenu

Le contrôle cherche la chaîne du secret **partout** dans l'image, et pas
seulement à son chemin d'origine.

Chercher un chemin se contourne en déplaçant le fichier, et ce contournement
n'apprend rien : ce qui compte est que le secret ne soit nulle part. Un lab qui
noterait le chemin enseignerait à ranger un secret ailleurs plutôt qu'à ne pas
le faire entrer.

## L'état de départ est cassé, et c'est la règle du dépôt

La construction de départ **échoue**, et le script attendu n'existe pas : les
quatre contrôles sont donc faux avant tout travail. Une tâche du setup vérifie
que la construction échoue bien, que le script est absent, et que le fichier
partagé et le secret sont à leur place : sans elle, un passage mal nettoyé
rendrait le lab déjà résolu.

## Un piège du cleanup, payé d'avance

Le dépôt part **en entier** : il porte le Dockerfile corrigé, le script, et le
cas échéant une copie du fichier partagé. Et le **cache du constructeur** part
avec, que `docker image prune` ne touche pas : les contrôles de ce lab
reconstruisent, et un cache survivant servirait une image dont le contexte n'est
plus celui qu'on mesure.

## Ce que le lab n'exige pas

Un chemin. Le Dockerfile peut être désigné par une option ou déplacé,
l'exclusion peut passer par un fichier dédié ou par des copies ciblées. Le jeton
et la version sont tirés par le setup et relus dans le dépôt au moment de la
notation : rien n'est écrit en dur dans les contrôles.
