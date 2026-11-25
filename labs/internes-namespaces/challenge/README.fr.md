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

## Mission

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le conteneur
`cloisonne` **tourne déjà**, et son processus principal exécute
`sleep 987654`, une commande qui ne sert à rien sinon à être reconnaissable.

Les trois premières réponses vont dans `/opt/lab-namespaces/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

### 1. Le PID du processus sur l'hôte

À la ligne `pid_hote=`.

Le processus principal du conteneur est le PID 1 **à l'intérieur**, et il porte
aussi un PID sur l'hôte, puisqu'il est un de ses processus. Rien n'a été
dupliqué : c'est une numérotation différente du même objet.

Le PID change à chaque démarrage. Il n'y a rien à recopier d'un passage
précédent.

### 2. L'identifiant du namespace PID de `cloisonne`

À la ligne `ns_pid=`, de la forme `pid:[...]`.

Un namespace n'a pas de nom : il a un **numéro d'inode**, que le noyau expose
par un lien dans `/proc/<pid>/ns/`. Le donner suppose d'avoir trouvé où ils
vivent, ce qui est le préalable de toute enquête sur l'isolation.

Attention à lire celui du processus du **conteneur**, pas celui de l'hôte :
celui de l'hôte serait celui dont ce namespace est isolé.

### 3. Le namespace partagé avec l'hôte

À la ligne `partage=`, l'identifiant complet, de la forme `nom:[...]`. Le
nom seul ne suffit pas : il est dans la leçon, l'inode n'est que sur votre
machine, et il est identique des deux côtés.

Il y en a sept : `pid`, `net`, `mnt`, `uts`, `ipc`, `user`, `cgroup`. **Six
diffèrent entre le conteneur et l'hôte. Un est identique.**

Comparez les namespaces de `cloisonne` à ceux du processus 1 de l'hôte. Celui
qui est partagé est aussi celui qui explique pourquoi root dans un conteneur est
un sujet de sécurité.

### 4. Un conteneur qui voit les processus de l'hôte

Lancez un conteneur nommé `indiscret` qui **voit** le `sleep 987654` de son
voisin.

Par défaut, un conteneur a sa propre vue des processus et ne voit que les siens.
Il faut y renoncer.

Le contrôle vérifie que le processus est vu **sous le PID de l'hôte**. C'est ce
qui distingue « il voit les processus de l'hôte » de « il voit les siens », que
rien d'autre ne sépare.

### Un conseil d'outillage

`readlink /proc/<pid>/ns/<nom>` affiche l'identifiant d'un namespace. Et
`readlink /proc/1/ns/<nom>` donne celui de l'hôte, pour comparer.

Il faut être root pour résoudre ces liens : c'est normal, et ce n'est pas le
sujet du lab.

### Ce qui n'est pas noté

La commande que vous avez tapée. Le PID se lit par le moteur comme dans la liste
des processus de l'hôte, et les namespaces par plusieurs outils. Seul l'état
compte.
