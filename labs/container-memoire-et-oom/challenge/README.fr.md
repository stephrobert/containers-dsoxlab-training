# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-container-memoire-et-oom`.

Gardez `worker` actif dans le projet `dsoxlab-container-memoire-et-oom`, avec
son label `dsoxlab.lab=container-memoire-et-oom`. Gardez aussi les garde-fous
pids et CPU du projet. Ni modification du swap hôte, ni allocateur non borné.

Quatre contrôles indépendants mesurent quatre choses différentes.

## 1. Les limites déclarées bornent la mémoire et interdisent le swap

`Memory` et `MemorySwap` valent tous deux 33554432, soit 32 Mio.

C'est l'égalité des deux qui interdit le swap, et la distinction n'est pas
cosmétique. Mesuré sur l'hôte du lab, dans les deux vues :

| Forme | `MemorySwap` déclaré | `memory.swap.max` |
| --- | --- | --- |
| `--memory 32m` seul | 67108864, soit le **double** | 33554432 |
| `--memory-swap` égal | 33554432 | **0** |
| `--memory-swap -1` | -1 | `max` |

Un `--memory` posé seul ne laisse donc pas le swap « ouvert » : Docker double la
valeur, et le cgroup accorde un budget de swap **égal à la mémoire**. L'illimité
n'arrive qu'avec `-1`. Seule l'égalité des deux met `memory.swap.max` à 0.

À noter, parce que cela change ce qu'on peut en conclure : l'hôte de ce lab n'a
**aucun swap**. Une allocation n'y déborde donc nulle part, quelle que soit la
valeur, et c'est le contrat de déploiement qui exige l'égalité, non un
débordement qu'on pourrait observer ici.

Ce contrôle n'exige rien sur `OomKillDisable`, et c'est mesuré : sur un hôte
en cgroup v2, le noyau ne sait pas désactiver l'OOM killer. Docker écarte
l'option avec un avertissement et le champ ne vaut même pas `false`. Une
exigence qui ne peut pas être violée ne contrôle rien ; ce qu'elle visait est
mesuré par le contrôle 3, qui observe un OOM réel. Un OOM compté **est** la
preuve que le tueur est actif.

## 2. Le cgroup applique vraiment la borne

Dans le conteneur, `memory.max` vaut 33554432 et `memory.swap.max` vaut 0.

Le contrôle précédent lit ce qu'on a **demandé** au démon, celui-ci ce que le
noyau a **retenu**. Une déclaration que le noyau n'a pas retenue ne borne rien,
et c'est le cgroup qui fait foi.

## 3. Une allocation excessive subit un OOM réel

Une sonde bornée est lancée dans le conteneur. Elle doit être tuée, et surtout
le compteur `oom_kill` de `memory.events` doit **augmenter**.

Un code de sortie non nul ne prouve rien par lui-même : une commande peut
échouer pour mille raisons. C'est `memory.events` qui dit que le noyau a tué
l'allocation, et c'est donc lui qu'on lit, avant et après.

La sonde est bornée à dessein. Un allocateur sans fin stresserait l'hôte, ce que
le scénario interdit, et mesurerait l'OOM killer global au lieu de celui du
cgroup.

Sa taille est **mesurée**, et c'est moins trivial qu'il n'y paraît : elle doit
être tuée sous 32 Mio *et survivre* sous les 96 Mio du départ, sinon elle
déclare la mission accomplie avant tout travail.

La sonde double une chaîne à chaque tour, si bien qu'au dernier tour elle
détient l'ancienne et la nouvelle : sa consommation de pointe dépasse donc la
taille annoncée. De combien, cela se mesure. Relevé dans `memory.peak` du
cgroup, le rapport entre la pointe et la taille tend vers **1,53**, et non
vers 2 comme une lecture rapide du doublement le laisse croire. Une sonde de
32 Mio pointe à 49 Mio : au-dessus de 32, sous 96.

## 4. Le service survit à l'OOM et garde son état

Trois choses, après un OOM provoqué par ce contrôle : le worker tourne encore,
son `StartedAt` n'a pas changé, et un reçu écrit **avant** l'incident se relit
après.

C'est l'autre moitié de l'exigence, et la plus facile à perdre. Un budget qui
emporte le PID 1 à chaque pic ne protège pas le service, il le remplace par un
redémarrage. Survivre comme processus ne suffit pas non plus : un service qui
repart de zéro a perdu ce qu'il tenait.

Ce contrôle provoque **sa propre** sonde plutôt que de réutiliser celle du
contrôle 3. Un contrôle qui suppose qu'un autre a déjà tourné mentirait dès
qu'on le joue seul, et c'est aussi pourquoi il vérifie lui-même qu'un OOM a bien
eu lieu : sans incident, la survie ne se distingue pas du fait que rien ne s'est
produit.

## Ce qui n'est pas noté, et pourquoi on vous le dit

Trois vérifications précèdent les mesures sans être des exigences : qu'un seul
`worker` tourne, qu'il porte son label, et que l'hôte ait assez de mémoire
libre. Sans elles, aucun contrôle ne peut observer quoi que ce soit, et un
contrôle qui n'a pas pu regarder ne doit jamais conclure au vert.

Les deux dernières ne dépendent même pas de vous. Si la marge de l'hôte est
insuffisante, la sonde risque d'être tuée par l'OOM killer **global** et non par
celui du cgroup : le contrôle mesurerait la machine au lieu de votre travail.
Le message vous dit alors que ce n'est pas votre faute, et ce qu'il faut libérer.

Enfin, la conservation du reçu pendant l'incident ne dit rien d'une survie à un
redémarrage de la machine : ce n'est pas ce que ce lab mesure.
