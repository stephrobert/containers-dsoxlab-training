# troubleshoot-conflit-de-port : deux messages, deux mondes

## Ce que ce lab éprouve

Que deux conflits de port qui se ressemblent n'ont pas la même cause, et que les
outils Docker sont **aveugles** à l'une des deux.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Coupable | Message du moteur | `docker ps` le voit | `ss` le voit |
| --- | --- | --- | --- |
| un conteneur | « port is already allocated » | **oui** | oui, `docker-proxy` |
| un processus de l'hôte | « Error starting userland proxy: listen » | **non** | oui, le programme |

Les deux messages diffèrent, et c'est la clé. Le premier vient du **moteur**,
qui sait ce qu'il a déjà réservé ; le second vient du **système**, qui refuse
l'écoute. Un dépanneur qui lit cette différence sait immédiatement s'il doit
chercher dans Docker ou en dehors.

Mesuré aussi : le conteneur refusé est **créé quand même**, statut `created`, et
il occupe donc son nom. C'est pourquoi un second essai échoue sur « name already
in use » et fait croire à une autre panne.

Et ce qui n'est **pas** un conflit : deux conteneurs peuvent publier le même
port **de conteneur** sur deux ports d'hôte différents. C'est le port de l'hôte
qui est unique.

## Deux fautes de conception corrigées par le cycle de validation

Ce lab a été rouge deux fois, et les deux fois pour la **même racine** : une
valeur de diagnostic ne peut pas se lire sur un objet que la réparation modifie.

**Première version.** Le lab demandait de rendre aux intrus le port qu'ils
réclamaient, donc de libérer celui du coupable. À la notation, le coupable du
port n'était plus `occupant` mais l'intrus lui-même, et les réponses des
contrôles 2 et 3 devenaient fausses. Le lab se contredisait.

La correction n'est pas technique, elle est **pédagogique** : libérer le port
est le geste spontané et le mauvais. Le lab demande donc de **déplacer** le
nouveau venu, ce qui laisse les coupables en place et les garde identifiables.

**Seconde version.** Le premier contrôle lisait encore le statut de `intrus-a`,
qui tourne après réparation. D'où le **témoin** : `temoin-refuse` échoue comme
les autres, l'énoncé demande expressément de ne pas le réparer, et le statut se
lit sur lui. Il reste vrai du début à la fin.

## Le quatrième contrôle vérifie les deux moitiés du remède

Les intrus tournent **ailleurs**, et les coupables sont **intacts**.

Sans la seconde moitié, la réponse la plus destructrice passerait : tout couper
ferait tourner les intrus et le lab enseignerait exactement ce qu'il faut
éviter. Rien ne disait que le conteneur en place et le programme de l'hôte
étaient inutiles.

## Un piège d'outil, rencontré pour la seconde fois

`pkill -f "nc -l -k -p 18201"` rend **`rc: -15`** : la ligne de commande du
shell qui porte le pkill contient le motif cherché, donc le shell se tue
lui-même avant d'avoir pu rendre 0, et `|| true` n'est jamais atteint.

La parade vient du monde de `ps | grep` : une lettre entre crochets. `n[c] -l -k
-p 18201` correspond à `nc -l -k -p 18201`, et la ligne du pkill contient
`n[c]`, que ce motif ne reconnaît pas.

C'est la seconde apparition de ce piège dans la section. Dans
`container-limite-cpu`, il avait été absorbé en acceptant le code 143, ce qui
était correct mais moins propre : ici le processus à tuer est **hors** des
conteneurs, et le laisser vivant tiendrait un port de l'hôte indéfiniment.

## Un geste du cleanup que ce lab est seul à devoir faire

Tuer un processus de l'**hôte**. Aucun autre lab du catalogue ne pose quoi que
ce soit en dehors des conteneurs, et un écouteur oublié tiendrait son port
indéfiniment : le lab suivant qui voudrait ce port échouerait sans rapport avec
son sujet.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | trois clés, trois valeurs **vides** | les renseigner | 1, 2 et 3 |
| `occupant` | tourne, tient un port | ne pas y toucher | 4 |
| un écouteur de l'hôte | écoute, hors de Docker | ne pas y toucher | 4 |
| `intrus-a`, `intrus-b` | créés, refusés | les déplacer | 4 |
| `temoin-refuse` | créé, refusé | **ne pas réparer** | 1 |

Le setup vérifie que les trois refusés ne tournent pas et que les deux ports
sont bien pris avant de rendre la main.

## Ce que le lab n'exige pas

Un chemin. Le coupable conteneur se trouve par la liste des conteneurs comme par
l'inspection, celui de l'hôte par n'importe quel outil qui lit les sockets, et
le déplacement se fait en recréant le conteneur sur un port libre, par n'importe
quel moyen.
