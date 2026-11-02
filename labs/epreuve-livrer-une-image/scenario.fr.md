# Scénario

Votre équipe livre une image à un partenaire. Il n'a pas votre dépôt, ni votre
cache, ni le droit d'écrire dans votre registre : il a une machine, la confiance
de votre autorité, et un compte en lecture seule.

La dernière livraison s'est mal passée de deux façons à la fois. L'image ne
démarrait pas chez lui, parce qu'elle dépendait d'un fichier qui n'existait que
sur la machine de construction. Et un auditeur a retrouvé le jeton de build dans
une couche, en lisant l'historique de l'image : il n'avait rien à décoder, c'était
écrit.

On vous demande de refaire la livraison, et de la rendre vérifiable.

## Mission

Construisez l'image sans que le secret de construction survive dans une couche,
publiez-la, consignez sa référence par digest, et faites-la tourner sur le client
nu par ce digest.

C'est une **épreuve** : le seuil de réussite est de 75 %. Le détail de ce qui
est attendu est dans `/opt/lab-livraison/MISSION.md`.
