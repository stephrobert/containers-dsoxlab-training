# internes-namespaces : une vue, pas un mur

## Ce que ce lab éprouve

Qu'un namespace est une **vue**, pas une barrière. Le PID 1 d'un conteneur est
un processus ordinaire de l'hôte, sous un autre PID, avec sa ligne de commande
lisible. Rien n'est caché à l'hôte : seul le conteneur a une vue restreinte.

C'est le premier lab de la section `conteneurs-isolation`, et il pose ce que les
neuf suivants supposent.

## La leçon de sécurité, mesurée avant d'être écrite

Sur `docker.lab`, le 2026-10-30 :

| namespace | isolé du conteneur |
| --- | --- |
| `pid`, `net`, `mnt`, `uts`, `ipc`, `cgroup` | oui |
| **`user`** | **non, partagé avec l'hôte** |

`user:[4026531837]` est identique des deux côtés. Conséquence : l'utilisateur 0
du conteneur est l'utilisateur 0 de la machine.

Ce n'est pas une faille, c'est le réglage par défaut, et c'est ce qui rend
nécessaires toutes les précautions que la section suivante enseigne. Le lab fait
**trouver** ce namespace plutôt que de l'annoncer, parce qu'on ne se méfie bien
que de ce qu'on a constaté soi-même.

## Aucune valeur n'est écrite dans les tests

Le PID est demandé au moteur, les identifiants de namespace sont lus dans
`/proc`, et le namespace partagé est trouvé **par comparaison**.

C'est une décision, pas une commodité : le jour où Docker activera l'isolation
des utilisateurs par défaut, le troisième contrôle **suivra** au lieu de devenir
faux. Une liste écrite d'avance aurait transformé une mesure en dogme.

La solution de référence applique la même règle, et c'est ce qui en fait une
démonstration de méthode : elle cherche le namespace partagé en comparant les
sept, au lieu d'écrire `user`.

## Le quatrième contrôle regarde l'effet, pas l'option

Lire `.HostConfig.PidMode` serait plus simple et noterait l'**intention**.
Vérifier que le conteneur voit le processus de son voisin note le **résultat**,
et accepte tout chemin qui y mène.

Il vérifie en outre le PID sous lequel il le voit : celui de l'**hôte**. C'est
ce qui distingue « il voit les processus de l'hôte » de « il voit les siens »,
que rien d'autre ne sépare, puisque les deux donnent une liste non vide.

## Pourquoi la commande du conteneur est un marqueur

`sleep 987654` n'a aucune utilité pour le conteneur. Elle sert à être
reconnaissable dans la liste des processus de l'hôte, où elle apparaît telle
quelle, et l'énoncé la nomme.

Chercher une aiguille sans savoir à quoi elle ressemble n'enseignerait rien du
sujet : le sujet est que l'aiguille **soit visible**, pas qu'elle soit difficile
à trouver.

## L'élévation est indispensable ici

`lab_host()` ouvre la machine avec `sudo=true`, et pour une fois ce n'est pas
une commodité : les liens de `/proc/<pid>/ns/` ne sont résolvables que par root.
Un lab qui aurait mesuré sans élévation aurait rendu des chaînes vides et
accusé l'apprenant.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | trois clés, trois valeurs **vides** | les renseigner | 1, 2 et 3 |
| `cloisonne` | tourne, isolé | ne pas y toucher | tous |
| *rien* | `indiscret` absent | le lancer avec la vue de l'hôte | 4 |

Une tâche du setup **vérifie** cet état avant de rendre la main : `cloisonne`
tourne avec son marqueur, et `indiscret` n'existe pas encore.

## Ce que le cleanup retire, bien que le setup ne le crée pas

`indiscret`. C'est l'apprenant qui le lance, et le laisser derrière rendrait le
quatrième contrôle vrai au passage suivant avant tout travail.

Rien d'autre à nettoyer, et c'est notable : ce lab ne crée ni volume, ni réseau,
ni image. Il ne fait que regarder, ce qui est exactement son sujet.

## Ce que le lab n'exige pas

Un chemin. Le PID se lit par le moteur comme dans la liste des processus de
l'hôte ; les namespaces par `readlink` comme par `lsns` ; et la vue des
processus s'obtient à la création du conteneur, quelle que soit la façon de le
créer.
