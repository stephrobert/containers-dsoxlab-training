# Scénario

Un client appelle : le service ne répond plus. Vous ouvrez la console de l'hôte
qui le portait, et ce que vous voyez ne ressemble à rien de ce que vous attendiez.

La décision est prise avant que vous ayez fini de regarder : cet hôte n'est plus
de confiance, le service repart ailleurs. Vous avez l'autre machine, le fichier
de la pile, l'image, et une sauvegarde prise avant la panne.

Vous avez aussi une consigne que personne ne répétera : la base de données
n'était joignable que par l'API, et elle doit le rester. C'est ce qui a été
écrit dans le dossier de sécurité, et c'est ce qui sera relu si l'incident monte.

## Mission

Établissez l'état réel, remontez le service sur l'autre hôte, restaurez
l'enregistrement témoin, et ne perdez pas l'isolement du réseau de données en
chemin.

C'est une **épreuve** : le seuil de réussite est de 75 %. Le détail de ce qui
est attendu est dans `/opt/lab-restauration/MISSION.md`, sur l'hôte où le
service doit repartir.
