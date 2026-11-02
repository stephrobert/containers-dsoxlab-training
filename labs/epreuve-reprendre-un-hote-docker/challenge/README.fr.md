# Épreuve : reprendre un hôte Docker

Cet hôte n'a pas été suivi. Le disque se remplit, la configuration du démon n'a
jamais été écrite, et personne ne sait qui peut encore lui parler.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. Le démon tourne avec une rotation des journaux

**Écrire `daemon.json` ne suffit pas** : le démon ne le relit qu'au redémarrage,
et la rotation s'applique aux conteneurs créés **ensuite**, jamais
rétroactivement.

Le contrôle crée donc un conteneur jetable et lit sa configuration de
journalisation : c'est le seul endroit où la rotation est un fait et non une
intention. Et l'application doit tourner : redémarrer le démon arrête les
conteneurs sans politique de redémarrage et ne les relance pas.

### 2. La place est rendue, et le volume utile est intact

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Deux faces inséparables. Les conteneurs arrêtés, les volumes anonymes orphelins
et le cache de build sont ce qu'un hôte non suivi accumule, et ils ne servent à
personne.

Mais **les deux volumes nommés doivent rester, avec leurs données**. Celui de
l'application est monté, donc tout `prune` l'épargne. Celui des sauvegardes
n'est monté par personne : c'est lui qu'un `docker volume prune -a` emporte, là
où un `prune` sans `-a` ne prend que les volumes anonymes. C'est la perte qu'on
voit en production. **Un volume non monté n'est pas un volume inutile.**

Pas d'images pendantes ici, et c'est une mesure qui l'impose : sur le magasin
containerd de cette version, une image dont la référence disparaît est ramassée
aussitôt. La notion vient du magasin classique et n'a plus d'objet.

### 3. Le groupe docker ne porte que ceux qui doivent y être

Trois faits, et le troisième est celui qu'on oublie : le stagiaire sort,
l'exploitant reste, et **personne d'autre n'a bougé**. Un retrait appliqué trop
large emporte aussi le compte qui administre la machine : le travail a l'air
fait, et l'hôte devient inaccessible à qui en a besoin.

### 4. L'outil passe par un proxy de lecture seule

**Un socket n'est pas un fichier.** Un montage `:ro` porte sur l'inode, pas sur
ce qui circule : tout ce qui parle au socket peut créer, arrêter et supprimer,
donc faire sur l'hôte tout ce que le démon peut faire.

Deux faits sont mesurés : l'outil ne monte plus le socket, **et** le proxy refuse
une requête d'arrêt tout en laissant passer une lecture. Le second est le vrai
contrôle : un proxy qui laisserait tout passer satisferait le premier sans rien
protéger.

### 5. Aucun socket TCP sans TLS

Une API Docker en TCP sans TLS donne à quiconque l'atteint le pouvoir de lancer
un conteneur privilégié, donc de devenir root sur la machine.

Le contrôle regarde les **sockets d'écoute** et la **ligne de commande effective
du démon**, et non un fichier de configuration : corriger un fichier sans
redémarrer laisse l'écoute en place, et fermer une écoute sans corriger ce qui
lance le démon la fait revenir au prochain démarrage.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
