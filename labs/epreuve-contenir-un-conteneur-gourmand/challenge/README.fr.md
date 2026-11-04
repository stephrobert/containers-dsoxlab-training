# Épreuve : contenir un conteneur gourmand

Le conteneur `traitement` s'emballe la nuit, ralentit la machine, se fait tuer,
et laisse des fichiers incomplets. Il écrit dans `/resultats`, porté par un
volume **qui contient déjà des résultats**.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. Trois limites, posées et appliquées

Mémoire, processeur, nombre de processus. Chacune est lue à **deux endroits** :
l'inspection dit ce que le moteur a **retenu**, le cgroup dit ce que le noyau
**applique**. Les deux peuvent différer, et c'est pourquoi les deux sont lues.

Une précision qui change l'ordre de vos gestes : **deux voies** posent ces
limites, et les deux marchent. Recréer le conteneur, ou `docker update` sur
celui qui tourne. Mesuré sur cette machine, Docker 29.9.2 : un `docker update
--memory 64m --memory-swap 64m --cpus 0.5 --pids-limit 50` rend 0, l'inspection
porte les nouvelles valeurs, le cgroup les applique (`memory.max=67108864`,
`pids.max=50`, `cpu.max=50000 100000`) et `StartedAt` ne change pas.

### 2. La pointe est contenue

Lire une limite ne dit pas si elle contient quoi que ce soit. Le contrôle
déclenche la pointe, puis lit `memory.peak` et `memory.events` : le pic ne doit
pas dépasser la limite, et la limite doit avoir été **atteinte**, sans quoi la
pointe n'a pas eu lieu et le contrôle ne mesurerait rien.

Et l'hôte ne doit avoir perdu aucun processus. C'est le vrai sujet : un
conteneur sans limite ne se punit pas lui-même, **il punit son voisin**.

### 3. Le traitement répond encore

**Contenir n'est pas tuer.** Une limite bien posée tue le processus gourmand,
pas le service. Ce contrôle est séparé du précédent parce que sa cause est
différente : il échoue avec une limite parfaitement posée mais trop basse.

### 4. Les résultats antérieurs sont intacts, et rien n'est tronqué

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Le contrôle compare des **empreintes**, pas des noms : c'est ce qui distingue
« les fichiers sont là » de « les fichiers sont intacts ». Un volume recréé vide,
puis regarni par le traitement, porterait des noms plausibles et un contenu
différent.

### 5. Le relevé dit le PID hôte et le runtime

Le PID hôte du PID 1 est la **jointure entre les deux mondes** : le processus qui
se croit numéro un dans son conteneur porte un autre numéro sur la machine, et
c'est celui-là qu'on voit dans `ps`, dans `top` et dans un journal du noyau. Qui
ne sait pas faire cette jointure ne peut pas rattacher une trace de l'hôte à un
conteneur.

Le contrôle **recalcule** les deux valeurs : il n'en garde aucune en dur.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**. Aucune valeur de limite n'est imposée.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
