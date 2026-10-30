# docker-premier-conteneur : trois verbes qui ne se recouvrent pas

## Ce que ce lab éprouve

Le cycle de vie d'un conteneur, et la seule idée qui compte à ce stade : **un
conteneur arrêté existe encore**. Lancer, arrêter et supprimer sont trois
gestes distincts, et les deux derniers sont confondus par presque tout le monde
une fois.

C'est le **lab d'entrée du catalogue**, et le backlog lui impose une contrainte
qu'aucun autre ne porte : se jouer en moins d'une minute, sans rien construire.
Un premier lab qui fait attendre décourage avant d'enseigner. Le setup pose
donc tout, y compris l'image, et il ne reste que trois commandes à taper.

## Pourquoi le setup pose DEUX conteneurs

Parce qu'un seul ne permettrait pas de noter les deux gestes séparément. Avec
un conteneur unique, un apprenant qui le supprime au lieu de l'arrêter obtient
un état indistinguable d'un ménage réussi.

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `vitrine` | `running` | l'arrêter | 3, et il refuse la suppression |
| `rebut` | `created` | le supprimer | 4 |
| *rien* | absent | lancer `premier` | 1 et 2 |

Le contrôle 3 distingue les deux fautes dans son message, parce qu'elles
appellent des gestes opposés : un conteneur encore en marche n'a pas été
arrêté, un conteneur disparu a été supprimé par excès de zèle.

## Les quatre contrôles, et pourquoi deux portent sur le même conteneur

`premier` en porte deux, qui mesurent des choses différentes : qu'il **tourne**
et que ses **journaux** portent une ligne imposée. Le second prouve qu'une
commande a été passée au conteneur, ce qui est le geste réel du CLI ; le
premier prouve qu'il est resté en vie, ce qui est le piège immédiat de
l'exercice, puisqu'un conteneur dont la commande se termine s'arrête aussitôt.

## L'état de départ est cassé, et c'est la règle du dépôt

Un test doit porter sur ce que l'état de départ ne porte PAS. Les quatre
contrôles sont donc faux au départ, et une tâche du setup le **vérifie** avant
de rendre la main : `vitrine running`, `rebut created`, et aucun `premier`.
Sans ce contrôle, un passage précédent mal nettoyé rendrait le lab déjà résolu
avant d'être posé.

## Alpine plutôt que l'image Debian déjà présente

Pour ne dépendre d'aucun autre lab, et pour que le `cleanup` puisse retirer son
image sans risquer d'emporter `debian:13`, dont `images-identifier-image` a
besoin. Un lab qui nettoie l'état d'un autre est une panne qui se découvre
ailleurs, et personne ne la rattache à sa cause.

L'image est épinglée par digest, puis taguée `lab-base:1.0` sur la machine : le
digest ne se recopie pas de mémoire, et la mission ne demande pas de le faire.

## Ce que le cleanup doit retirer, et qu'on oublie

Les **trois** conteneurs, `premier` compris, que le setup ne crée pas. C'est le
travail de l'apprenant, et le laisser derrière ferait hériter le lab suivant
d'un conteneur qu'il n'a pas posé. L'image se retire par ses **deux**
références, le tag local et le digest : ne retirer que le tag laisserait une
entrée sans nom dans l'inventaire du moteur, donc un écart que le validateur
refuse.
