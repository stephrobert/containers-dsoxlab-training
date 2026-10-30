# container-limite-cpu : brider, et le prouver

## Ce que ce lab éprouve

Qu'il y a **deux** façons de limiter le processeur d'un conteneur, qu'elles
n'ont pas le même effet, et que la plus employée ne change **rien** à ce que le
conteneur croit avoir.

## Mesuré avant d'être écrit

Sur `docker.lab`, machine à 2 CPU, le 2026-10-30 :

| Option | `cpu.max` | `cpuset.cpus` | `nproc` **dans** le conteneur |
| --- | --- | --- | --- |
| aucune | `max 100000` | tous | 2 |
| `--cpus 0.5` | `50000 100000` | tous | **2** |
| `--cpuset-cpus 0` | `max 100000` | `0` | **1** |

Et sous deux boucles infinies : le moteur annonçait **48,97 %**, le cgroup
comptait **85 étranglements**.

## Le piège du sujet est sur la deuxième ligne

Une limite de **temps** n'est pas une restriction de **vue**. Le conteneur bridé
à la moitié d'un CPU en voit toujours deux.

Une application qui dimensionne ses fils d'exécution sur ce nombre en lance donc
deux fois trop, et passe son temps à se faire étrangler. **C'est une cause réelle
de lenteur inexpliquée**, et elle ne se devine pas : les métriques de la machine
sont calmes, celles du conteneur montrent qu'il consomme ce qu'on lui a accordé.

Le lab fait poser la question au conteneur lui-même, parce que c'est la seule
façon de voir le malentendu plutôt que de l'apprendre.

## Le quatrième contrôle demande une preuve, pas une déclaration

Le cgroup compte les étranglements. Tant que `nr_throttled` est à zéro, la
limite n'a **jamais mordu** : elle est peut-être juste, elle n'est pas prouvée.

C'est la différence entre lire une configuration et constater un comportement.
Un lab qui se serait contenté de lire `cpu.max` aurait validé une limite
théorique, ce qui est exactement ce que l'exploitation ne peut pas se permettre.

## Deux boucles, et non une

La charge est le geste le plus délicat du lab, et il mérite son explication.

La première boucle consomme ce que la limite accorde ; la seconde force
l'étranglement. **Une seule pourrait tenir sous le plafond** sur une machine
rapide, et le compteur resterait à zéro, ce qui ferait croire à un lab cassé.

La solution de référence en lance donc deux, et les arrête ensuite : les laisser
tourner laisserait la machine chaude pour le lab suivant, que le cycle de
validation enchaîne trois fois.

## Un piège d'outil, mesuré

`pkill -f 'while :'` **se tue lui-même** : le motif correspond aussi au shell qui
porte la commande, et ce shell est tué avant d'avoir pu rendre 0. Le code
obtenu est 143, c'est-à-dire un SIGTERM reçu, et `|| true` n'y change rien.

La solution accepte donc explicitement 0 et 143, en disant pourquoi. Masquer le
code aurait été plus court et aurait caché un fait utile : ce 143 est la preuve
que le ménage a eu lieu.

## Aucune valeur n'est écrite en dur

Le quota attendu est lu dans le cgroup, le nombre de CPU est demandé à la
machine, et le troisième contrôle exige seulement que le conteneur épinglé en
voie **moins**.

Un test qui aurait porté `50000 100000` ou `2` serait faux sur une machine
différemment dotée. Et sur une machine à huit CPU, épingler sur deux est une
réponse aussi juste que sur un : le lab ne l'interdit pas.

## Deux préalables qui évitent d'accuser l'apprenant

La machine doit être en cgroup v2, sans quoi les noms de fichiers diffèrent. Et
elle doit offrir **au moins deux CPU** : sur une machine à un seul processeur,
épingler n'y changerait aucune vue, et le troisième contrôle serait vrai avant
tout travail.

Le setup vérifie les deux avant de poser le lab.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | deux clés, deux valeurs **vides** | les renseigner | 1 et 2 |
| `brideur` | bridé, **au repos** | le mettre sous charge | 4 |
| *rien* | `epingle` absent | le lancer épinglé | 3 |

Au repos, précisément pour que le compteur d'étranglements soit à zéro et que le
travail de l'apprenant s'y voie. Le setup le vérifie.

## Ce que le cleanup doit retirer

Les conteneurs, et **c'est le compteur qui le rend indispensable** : il vit dans
le cgroup, et le cgroup part avec le conteneur. S'il survivait, le quatrième
contrôle serait vrai au passage suivant avant tout travail.

## Ce que le lab n'exige pas

Un chemin. La charge se produit par une boucle de shell comme par n'importe quel
outil de saturation, et les deux options de limitation se posent à la création du
conteneur, quelle qu'en soit la façon.
