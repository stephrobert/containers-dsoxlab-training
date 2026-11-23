# Reprendre un hôte Docker que personne n'a suivi

Cet hôte tourne depuis deux ans et personne ne s'en occupe plus. La personne qui
l'avait monté est partie. Le disque se remplit, la configuration du démon n'a
jamais été écrite, et plus personne ne sait qui peut encore lui parler.

On vous demande de le reprendre.

## Ce qui est attendu à la fin

1. `/etc/docker/daemon.json` est **valide** et impose une **rotation** des
   journaux ; le démon a été **redémarré** pour la prendre ; un conteneur créé
   **ensuite** porte bien cette rotation ; et l'application `application` tourne
   toujours.
2. La place occupée pour rien est rendue : plus aucun **conteneur arrêté** du
   projet, plus aucun **volume anonyme** orphelin, et le cache de build purgé.
   **Les deux volumes nommés sont intacts**, avec leurs données : celui de
   l'application, `dsoxlab-reprise-donnees`, et celui des sauvegardes,
   `dsoxlab-reprise-sauvegardes`, que personne ne monte.
3. Le compte `stagiaire-parti` n'est plus dans le groupe `docker`, le compte
   `exploitant` y est toujours, et **personne d'autre** n'a été ni ajouté ni
   retiré.
4. L'outil `inventaire-outil` ne monte **plus** le socket du démon : il passe par
   le proxy de lecture seule que ce lab fournit, l'image `lab-reprise-proxy:1.0`.
   À travers ce proxy, une requête de **lecture passe** et une requête
   d'**arrêt est refusée**.
5. Le démon n'écoute plus **aucun socket TCP**, avec ou sans TLS : l'accès
   distant passe par le proxy fourni, pas par l'API du démon.

Le proxy doit être **joignable depuis l'hôte** : publiez-lui un port sur la
boucle locale. Il écoute sur le port 2375 dans son conteneur, et il a besoin du
socket du démon pour travailler.

L'énoncé complet est aussi sur la machine, dans `/opt/lab-reprise/MISSION.md`.

## Ce que vous n'avez pas à écrire

Les deux images sont fournies, `lab-reprise:1.0` et `lab-reprise-proxy:1.0`. Il
n'y a **rien à construire** : l'épreuve est de se servir du proxy, pas d'en
écrire un.

Le mode rootless n'est pas au programme de cette épreuve.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune commande
n'est imposée.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**perdre un volume nommé fait échouer l'épreuve**, même avec tout le reste en
place. Pour reprendre de la place, les commandes qui viennent à l'esprit
sont les `prune`, et toutes ne prennent pas la même chose.

Attention au volume des sauvegardes : il n'est monté par personne, parce qu'on
ne monte un volume de sauvegarde que pour sauvegarder. Un `prune` épargne
toujours ce qui est monté, et il distingue ensuite deux familles : sans `-a`, il
ne retire que les volumes **anonymes** ; avec `-a`, il retire aussi les volumes
**nommés** que rien ne monte. C'est `docker volume prune -a` qui emporte celui
des sauvegardes, mesuré sur cette version, et le moteur le dit dans
l'avertissement qu'il affiche avant d'agir. **Un volume non monté n'est pas un
volume inutile.**

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.

## Épreuve : reprendre un hôte Docker

Cet hôte n'a pas été suivi. Le disque se remplit, la configuration du démon n'a
jamais été écrite, et personne ne sait qui peut encore lui parler.

### Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

#### 1. Le démon tourne avec une rotation des journaux

**Écrire `daemon.json` ne suffit pas** : le démon ne le relit qu'au redémarrage,
et la rotation s'applique aux conteneurs créés **ensuite**, jamais
rétroactivement.

Le contrôle crée donc un conteneur jetable et lit sa configuration de
journalisation : c'est le seul endroit où la rotation est un fait et non une
intention. Et l'application doit tourner : redémarrer le démon arrête les
conteneurs sans politique de redémarrage et ne les relance pas.

#### 2. La place est rendue, et le volume utile est intact

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

#### 3. Le groupe docker ne porte que ceux qui doivent y être

Trois faits, et le troisième est celui qu'on oublie : le stagiaire sort,
l'exploitant reste, et **personne d'autre n'a bougé**. Un retrait appliqué trop
large emporte aussi le compte qui administre la machine : le travail a l'air
fait, et l'hôte devient inaccessible à qui en a besoin.

#### 4. L'outil passe par un proxy de lecture seule

**Un socket n'est pas un fichier.** Un montage `:ro` porte sur l'inode, pas sur
ce qui circule : tout ce qui parle au socket peut créer, arrêter et supprimer,
donc faire sur l'hôte tout ce que le démon peut faire.

Deux faits sont mesurés : l'outil ne monte plus le socket, **et** le proxy refuse
une requête d'arrêt tout en laissant passer une lecture. Le second est le vrai
contrôle : un proxy qui laisserait tout passer satisferait le premier sans rien
protéger.

#### 5. Aucun socket TCP, avec ou sans TLS

Une API Docker en TCP sans TLS donne à quiconque l'atteint le pouvoir de lancer
un conteneur privilégié, donc de devenir root sur la machine.

**Ajouter TLS ne suffit pas, et n'est pas ce qui est demandé.** Cette épreuve
fournit un socket-proxy et exige qu'il tourne : l'accès distant passe par ce
proxy filtrant, et l'API du démon n'a donc aucune raison d'être exposée en TCP,
chiffrée ou non. Ce qui n'a pas de raison d'exister ne se durcit pas, il se
retire.

Le contrôle regarde les **sockets d'écoute** et la **ligne de commande effective
du démon**, et non un fichier de configuration : corriger un fichier sans
redémarrer laisse l'écoute en place, et fermer une écoute sans corriger ce qui
lance le démon la fait revenir au prochain démarrage.

### Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
