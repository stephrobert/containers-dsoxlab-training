# epreuve-remettre-trois-conteneurs-en-service : l'épreuve du module de dépannage

## Ce que cette épreuve éprouve

Le diagnostic, trois fois, et par trois voies différentes. Elle clôt le module
« Observer et dépanner un conteneur » et ne réexplique rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## Les trois pannes, et elles n'ont pas la même cause

| Conteneur | Symptôme visible | Cause posée | Ce qu'elle enseigne |
| --- | --- | --- | --- |
| `collecteur` | sorti, ne redémarre pas | variable d'environnement manquante, sortie en **78** | un code de sortie se lit, et 78 veut dire « configuration invalide » |
| `expediteur` | redémarre sans fin | mode inconnu, sortie en **64**, politique `always` | la politique n'est pas la panne : elle la rend visible |
| `scribe` | dix secondes pour s'arrêter, rapport coupé | son PID 1 est un `sh`, qui ne transmet pas `SIGTERM` | qui est PID 1 décide de ce qui reçoit les signaux |

**C'est le point de l'épreuve** : une seule méthode de diagnostic, trois
conclusions distinctes. Un apprenant qui applique le même geste aux trois en
corrige au mieux une.

## Pourquoi la politique de redémarrage doit être conservée

C'est la fausse correction la plus tentante : retirer `--restart always` fait
disparaître le symptôme en une commande, et ne règle rien. Le conteneur sort
alors une fois et se tait, ce qui est pire qu'avant, puisque la panne devient
invisible.

Le contrôle exige donc les deux ensemble : plus de redémarrage, **et** la
politique en place. Et il mesure la stabilité **dans le temps**, par deux
lectures espacées de douze secondes : un compteur de redémarrages lu une seule
fois vaut zéro sur un conteneur qui vient d'être recréé, qu'il soit réparé ou
qu'il s'apprête à boucler.

## L'exigence critique

**Un rapport perdu ou tronqué fait échouer l'épreuve**, même à 80 points. Les
deux premières pannes coûtent du temps ; celle-là coûte une donnée.

Un rapport est complet quand il porte sa ligne de début **et** sa ligne de fin.
La ligne de fin n'est écrite que par le gestionnaire de fin du programme : elle
n'existe donc que si le programme a reçu son signal. C'est ce qui rend ce
contrôle juste, plutôt qu'arbitraire : il ne mesure pas une taille de fichier,
il mesure si le programme a pu finir son travail.

## Pourquoi l'ordre des contrôles n'est pas celui de l'énoncé

Le contrôle de l'arrêt propre doit **arrêter** le scribe : c'est la seule façon
de mesurer une durée d'arrêt et un code de sortie, et aucune lecture après coup
ne la remplace. Il est donc joué **en dernier**, après celui qui exige qu'aucun
conteneur ne traîne à l'arrêt.

L'ordre inverse ferait échouer ce dernier **à cause du test lui-même**, ce qui
est le défaut qu'un test ne doit jamais avoir : mesurer sa propre trace.

## Trois faits mesurés par un seul contrôle, et pourquoi

La durée de l'arrêt, le code de sortie et l'intégrité du rapport ont la **même
cause**. Les séparer donnerait trois contrôles pour une seule compétence, et le
barème pèserait trois fois le même acquis : un apprenant qui comprend les
signaux gagnerait trois cinquièmes de l'épreuve, un autre qui ne les comprend
pas en perdrait trois.

## Ce que l'épreuve ne mesure pas

Les volumes, les réseaux, la construction d'images. Rien de cela n'est au
programme de ce module.
