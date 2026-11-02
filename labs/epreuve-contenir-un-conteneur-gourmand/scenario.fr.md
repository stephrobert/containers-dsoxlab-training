# Le traitement qui emporte la machine avec lui

Le conteneur `traitement` exécute un traitement par lots. La nuit, il s'emballe :
la machine entière ralentit, il finit par se faire tuer, et il laisse derrière
lui des fichiers incomplets. Au matin, personne ne sait ce qui a été traité.

Il écrit ses résultats dans `/resultats`, porté par le volume
`dsoxlab-gourmand-resultats`. **Ce volume contient déjà des résultats, et ils ne
se reproduisent pas.**

## Ce qui est attendu à la fin

1. Le conteneur porte **trois limites**, visibles dans son inspection **comme
   dans son cgroup** : la mémoire, le processeur, et le nombre de processus.
2. Quand la pointe est déclenchée, elle est **contenue** : le conteneur ne
   dépasse pas sa propre limite mémoire, et **aucun processus de l'hôte n'est
   tué**.
3. Le traitement **répond encore** après la pointe.
4. Les résultats antérieurs sont **intacts**, et aucun fichier de `/resultats`
   n'est tronqué : chacun porte sa ligne de fin.
5. Le fichier `/opt/lab-gourmand/releve.txt` consigne deux faits, une ligne
   chacun :

   ```text
   pid_hote=<le PID, sur l'hôte, du processus PID 1 du conteneur>
   runtime=<le runtime par défaut du moteur>
   ```

**Pour déclencher la pointe** : créez le fichier `/tmp/pointe` **dans** le
conteneur, puis adressez-lui une requête. Le traitement l'évalue après chaque
requête servie. C'est un outil du lab, pas une énigme.

L'énoncé complet est aussi sur la machine, dans `/opt/lab-gourmand/MISSION.md`.

## Une précision sur la pointe

Elle est **bornée** : l'allocation plafonne à 256 Mo, et elle ne met pas la
machine en danger même sans limite. C'est délibéré : une épreuve ne doit pas
pouvoir emporter la machine qui la mesure.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune valeur de
limite n'est imposée : ce qui est mesuré est qu'une limite existe, qu'elle soit
appliquée par le noyau, et qu'elle contienne la pointe sans tuer le service.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**perdre les résultats antérieurs fait échouer l'épreuve**, même avec tout le
reste en place. C'est le piège, et il est entier : poser des limites exige de
**recréer** le conteneur, et c'est là qu'on oublie un volume.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
