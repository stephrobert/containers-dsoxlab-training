# Un espace de travail plein

## La situation

Sur `docker.lab`, le `worker` du projet `dsoxlab-troubleshoot-disque-plein` ne
peut plus rien écrire dans `/sandbox`. Ce dossier est un tmpfs de 16 Mio, pas une
partition de l'hôte. Il contient deux fichiers : `/sandbox/keep.txt`, un reçu à
garder, et `/sandbox/fill.bin`, un remplissage jetable. Le projet se trouve dans
`/opt/dsoxlab-troubleshoot-disque-plein`.

## Mission

Rendez `/sandbox` de nouveau inscriptible dans le conteneur **existant** :

- `/sandbox/fill.bin` est absent ;
- `/sandbox/keep.txt` porte toujours `keep-this-receipt` ;
- une écriture d'un Mio dans `/sandbox` aboutit.

Ne recréez pas le conteneur, n'agrandissez pas `/sandbox`, ne le remplacez pas
par un dossier de l'hôte, ne changez pas ses limites de mémoire et ne lancez
aucun prune global.

## Ce qui est noté

1. Le remplissage est parti et le reçu est intact.
2. Le contrôle écrit un Mio dans `/sandbox`, vérifie que le fichier pèse
   1048576 octets, puis retire sa sonde.

Franchir une interdiction fait échouer les deux contrôles, et le message la
nomme. Le plafond est lu dans le conteneur, par `df`.
