# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-troubleshoot-disque-plein`, dans
le `worker` **existant** du projet `dsoxlab-troubleshoot-disque-plein`.

Deux contrôles seulement, et c'est une contrainte, non un choix de confort.

## 1. Le remplissage jetable a été retiré, sans perdre le reçu

`/sandbox/fill.bin` est absent, et `/sandbox/keep.txt` porte encore son contenu
`keep-this-receipt`.

Les deux vont ensemble parce que ce sont les deux faces d'une même exigence :
récupérer de l'espace sans jeter ce qui compte. Vider le bac à sable en entier
récupère bien de l'espace, en détruisant ce que l'exercice demandait de
protéger.

## 2. L'espace récupéré permet une écriture réelle

Le contrôle écrit un Mio dans `/sandbox`, vérifie que le fichier pèse réellement
1048576 octets, puis retire sa sonde dans tous les cas.

Un `df` ne suffirait pas : un `dd` peut rendre un succès en ayant écrit moins que
demandé, et c'est la taille réelle du fichier qui tranche. Le setup garantit
l'état de départ en exigeant qu'une sonde de 4 Kio **échoue**, donc ce contrôle
refuse bien avant tout travail.

## Ce qui n'est pas noté, et pourquoi on vous le dit

Trois exigences de ce lab sont **déjà satisfaites au départ** : le conteneur
d'origine existe, `/sandbox` est un tmpfs de 16 Mio, et le reçu est présent. Ce
sont des exigences de **préservation**, pas des objectifs à atteindre.

Elles ne peuvent donc pas devenir des contrôles séparés : un contrôle qui passe
avant tout travail accorderait des points pour rien. Elles vivent dans le
garde-fou commun aux deux contrôles, qui refuse la triche sans rien donner, et
son message nomme l'interdiction franchie :

- recréer le conteneur, ce qui efface ses données au lieu de récupérer de
  l'espace ;
- relever le plafond du bac à sable, ce qui n'est pas récupérer de l'espace ;
- le faire pointer ailleurs qu'un tmpfs, ce qui écrirait dans une partition
  hôte.

Le plafond est lu dans le conteneur, par `df`, et non dans la déclaration : c'est
le système qui fait foi.
