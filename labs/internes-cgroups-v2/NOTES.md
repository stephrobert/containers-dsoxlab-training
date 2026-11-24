# internes-cgroups-v2 : compter et plafonner

## Ce que ce lab éprouve

Que l'isolation a **deux moitiés** qui n'ont rien à voir. Un namespace
restreint une **vue** ; un cgroup **compte et plafonne**. Le lab qui précède
montrait la première, celui-ci montre la seconde.

C'est le second lab de `conteneurs-isolation`, et les deux ensemble donnent le
vocabulaire que les huit suivants emploient.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Fait | Valeur |
| --- | --- |
| système de fichiers de `/sys/fs/cgroup` | `cgroup2fs`, pilote `systemd` |
| cgroup d'un conteneur | `/sys/fs/cgroup/system.slice/docker-<id>.scope` |
| `--memory 256m` donne `memory.max` | `268435456`, la valeur **en octets** |
| conteneur **sans** limite, `memory.max` | **`max`**, et non 0 ni un grand nombre |

Vérifié aussi, et c'est utile à savoir : le conteneur voit **sa propre limite**
dans son `/sys/fs/cgroup/memory.max`. C'est ainsi qu'une application bien élevée
se règle elle-même au lieu de supposer la mémoire de la machine.

## La troisième question est celle qui surprend

On cherche spontanément un nombre, et la réponse n'en est pas un.

L'absence de limite n'est pas une limite très haute : c'est l'**absence de la
notion**. C'est ce qui explique qu'un conteneur sans `--memory` puisse prendre
toute la mémoire de la machine, et c'est l'incident que le scénario raconte.

La poser comme question plutôt que l'affirmer est délibéré : constater soi-même
le contenu de ce fichier enseigne mieux qu'une phrase.

## Aucune valeur n'est écrite en dur

Ni dans les tests, ni dans la solution, pas même `max`.

Le chemin est construit depuis l'identifiant que le moteur donne, et chaque
limite attendue est **lue dans le cgroup**, pas recopiée de l'énoncé. Un test
qui aurait porté `268435456` serait faux le jour où le setup changerait de
limite, et le lab mourrait d'une modification sans rapport.

La solution applique la même règle, et c'est ce qui en fait une démonstration :
elle lit la troisième réponse au lieu d'écrire `max`.

## Le chemin est construit, pas cherché

Le moteur donne l'identifiant complet, et le pilote `systemd` en dérive un
chemin prévisible.

Un `find` dans `/sys/fs/cgroup` marcherait aussi, en plus lent et **moins
sûr** : deux conteneurs peuvent partager un préfixe d'identifiant, et un `find`
sur un préfixe rendrait alors le cgroup du voisin.

## Le préalable qui évite d'accuser l'apprenant

Sur une machine en cgroup v1, les chemins et les noms de fichiers diffèrent. Les
quatre contrôles échoueraient en parlant de limites, alors que la cause serait
la version du mécanisme.

Un garde-fou vérifie donc `cgroup2fs` avant toute mesure, et le **dit**. Le
setup fait le même contrôle, ce qui arrête le lab avant de le poser plutôt que
pendant la notation.

## Pourquoi deux limites sur `bride`, et non une

Une seule laisserait croire que la mémoire est le sujet. Elle n'en est qu'un
exemple.

Le nombre de processus protège d'une panne **différente** : celle qui remplit la
table des processus de la machine, où une limite mémoire ne changerait rien. Les
deux sont vérifiées dans le cgroup et non dans `.HostConfig` : ce que l'option a
demandé n'est pas ce que le noyau applique.

## L'élévation est indispensable ici

`lab_host()` ouvre la machine avec `sudo=true`, et ce n'est pas une commodité :
les fichiers du cgroup d'un conteneur ne sont pas lisibles par un compte
ordinaire.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | trois clés, trois valeurs **vides** | les renseigner | 1, 2 et 3 |
| `mesure` et `libre` | tournent, l'un limité l'autre non | ne pas y toucher | tous |
| *rien* | `bride` absent | le lancer avec deux plafonds | 4 |

Une tâche du setup **vérifie** cet état : `mesure` porte bien une limite,
`libre` n'en a aucune, et `bride` n'existe pas encore.

## Ce que le cleanup n'a pas à faire

Nettoyer les cgroups. Le noyau retire celui d'un conteneur quand le conteneur
disparaît, ce qui est une différence avec les volumes et les réseaux. Un lab sur
les cgroups ne peut pas laisser de dette sur la machine.

Il retire en revanche `bride`, que le setup ne crée pas : c'est l'apprenant qui
le lance, et le laisser rendrait le quatrième contrôle vrai au passage suivant.

## Ce que le lab n'exige pas

Un chemin. Les valeurs se lisent par `cat` comme par `docker exec` depuis le
conteneur lui-même, et les deux limites se posent à la création du conteneur,
quelle que soit la façon de le créer.
