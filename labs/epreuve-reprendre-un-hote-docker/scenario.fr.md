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
5. Le démon n'écoute plus **aucun socket TCP sans TLS**.

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
place. Pour reprendre de la place, la commande qui vient à l'esprit est
`docker system prune`, et l'une de ses options emporte les volumes.

Attention à celui des sauvegardes : il n'est monté par personne, parce qu'on ne
monte un volume de sauvegarde que pour sauvegarder. Un `prune` épargne ce qui est
monté et emporte le reste. **Un volume non monté n'est pas un volume inutile.**

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
