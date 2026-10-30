# « Le conteneur est isolé », mais isolé de quoi ?

## La situation

Vous présentez une architecture en conteneurs, et quelqu'un demande si c'est
sûr. La réponse qui vient toute seule est : « oui, les conteneurs sont isolés ».

C'est vrai, et c'est incomplet au point d'être trompeur. Un conteneur est isolé
dans un sens, et pas dans l'autre.

Ouvrez la liste des processus de la machine : le processus principal de chaque
conteneur y est, avec sa ligne de commande en clair. Rien n'est caché à l'hôte.
Ce qui est isolé, c'est **la vue du conteneur**, pas la machine.

Et parmi les sept cloisons que le noyau sait poser, Docker en pose six par
défaut. La septième change tout, et c'est celle que ce lab vous fait trouver.

## L'objectif

Regarder l'isolation depuis les deux côtés. Le conteneur `cloisonne` tourne, et
son processus principal exécute `sleep 987654`, une commande qui ne sert à rien
sinon à être reconnaissable.

Renseignez les trois lignes de `/opt/lab-namespaces/reponses.txt` :

```text
pid_hote=<le PID que ce MÊME processus porte sur L'HÔTE>
ns_pid=<l'identifiant du namespace PID de `cloisonne`, de la forme pid:[...]>
partage=<le NOM du seul namespace que `cloisonne` partage avec l'hôte>
```

Puis lancez un conteneur nommé `indiscret` qui **voit** les processus de l'hôte,
et donc le `sleep 987654` de son voisin.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Où chercher

Les namespaces d'un processus se lisent dans `/proc/<pid>/ns/`. Il y en a sept,
et chacun est un lien vers un numéro d'inode : c'est ce numéro qui identifie la
cloison.

Pour la troisième question, il suffit de **comparer** : les namespaces de
`cloisonne` d'un côté, ceux du processus 1 de l'hôte de l'autre. Six diffèrent.
Un est identique.

## Ce qui est noté

L'**état du système**. Le PID change à chaque démarrage et les identifiants de
namespace à chaque création : il n'y a rien à recopier d'un passage précédent,
et rien à apprendre par cœur.

Le quatrième contrôle regarde l'**effet** et non l'option : votre conteneur doit
voir le processus du voisin, **sous le PID de l'hôte**. C'est ce qui distingue
« il voit les processus de l'hôte » de « il voit les siens », que rien d'autre ne
sépare.

## Pourquoi cette troisième question mérite le détour

Le namespace partagé est celui des **utilisateurs**. Docker ne l'isole pas par
défaut, ce qui veut dire que l'utilisateur 0 du conteneur est l'utilisateur 0 de
la machine.

Ce n'est pas une faille : c'est le réglage par défaut, documenté, et c'est ce
qui rend nécessaires toutes les autres précautions que vous verrez plus loin
dans le parcours. On ne se méfie bien que de ce qu'on a constaté soi-même.
