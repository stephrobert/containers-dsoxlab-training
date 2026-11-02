# Rien ne tourne sur ce poste

Ce poste a été « installé » par quelqu'un qui est parti. Le moteur de conteneurs
y est bien présent, le paquet est là, et pourtant rien ne tourne. La première
commande que vous taperez ne répondra pas comme vous l'attendez.

Deux conteneurs traînent sur la machine, tous deux arrêtés. Ils sortent de la
même image. **L'un gêne, l'autre doit être préservé**, et rien ne les distingue
au premier regard.

## Ce qui est attendu à la fin

1. Le moteur est **en marche**, et il le restera **au prochain démarrage de la
   machine**.
2. Votre compte parle au moteur **sans `sudo`**.
3. Un conteneur nommé **`annuaire`** tourne, à partir de l'image
   `lab-mise-en-marche:1.0`, et **sa réponse porte** la valeur de configuration
   que la machine vous indique, passée par la variable d'environnement `SALLE`.
4. Le conteneur **`journal-de-bord`** est **conservé tel quel** : présent,
   **arrêté**, et ses journaux toujours lisibles. Il porte la trace d'un
   incident que l'exploitation doit pouvoir relire.
5. Le fichier `/opt/lab-mise-en-marche/prediction.txt` annonce, **sans jouer la
   commande**, ce que le moteur retiendra comme programme et comme arguments
   pour :

   ```bash
   docker run --rm lab-mise-en-marche:1.0 --verbeux
   ```

   Deux lignes, exactement sous cette forme :

   ```text
   path=<le programme effectif>
   args=<les arguments effectifs, séparés par une espace>
   ```

L'énoncé complet, avec la valeur de configuration à rendre, est sur la machine
dans `/opt/lab-mise-en-marche/MISSION.md`.

## Ce que vous n'avez pas à faire

L'image `lab-mise-en-marche:1.0` est fournie et porte le service : il n'y a
**rien à construire**. Ni volume, ni port publié : ce n'est pas le sujet de cette
épreuve.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune commande
n'est imposée : deux façons d'arriver au même état reçoivent la même note.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**si `journal-de-bord` est supprimé, ou redémarré, l'épreuve échoue**, même avec
tout le reste en place. Dans la vraie vie, le conteneur qu'un `docker rm` trop
large emporte est celui qui portait la trace de l'incident.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
