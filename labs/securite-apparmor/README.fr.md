# AppArmor

AppArmor ajoute une politique obligatoire fondée sur les chemins aux permissions
Unix. Un fichier lisible par tous peut encore être refusé. En mode `complain`,
un profil journalise les violations sans les bloquer ; `enforce` refuse
réellement l'accès.

Sur un projet jetable neutre `demo-notes`, comparez `AppArmorProfile` de
`docker inspect` avec `/proc/1/attr/current`. Une règle comme
`deny /notes/archive.txt r,` interdit la lecture de ce chemin, même si une règle
plus large `file,` autorise les fichiers.

Le profil pédagogique est volontairement large sauf pour un refus. Ce n'est pas
une politique de production. Les capabilities restent retirées et aucun chemin
hôte n'est monté. Setup exige AppArmor actif et `apparmor_parser` déjà installé.
Il refuse un profil préexistant portant le nom réservé, charge seulement son
nouveau profil sans écriture de cache et préserve la configuration système.
Aucune persistance après redémarrage n'est revendiquée.

Voir [le challenge](challenge/README.fr.md).
