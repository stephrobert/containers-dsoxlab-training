# L'image qui se construit, et dont personne ne peut se servir

## La situation

Le build est vert. L'image est dans le magasin local, le pipeline dit que tout
est passé, et l'équipe qui la reçoit la lance lundi matin.

À dix heures, trois choses ont mal tourné, et aucune ne se voyait la veille.
Un conteneur a démarré, mais rien ne répond sur le port qu'il publie. Un autre
refuse de dire pourquoi il s'est arrêté. Un troisième a été tué au bout de dix
secondes au lieu de s'arrêter, et le compteur qu'il gardait en mémoire est
parti avec lui.

Personne n'a testé l'image **de l'extérieur**, comme le font les gens qui la
font tourner. Les tests unitaires du code passaient, et ils ne pouvaient rien
attraper de tout cela : les défauts sont dans l'image, pas dans le programme.

## L'objectif

Le contexte est dans `/opt/dsoxlab-images-tester-le-contrat`. Le service qui s'y
trouve est un **guichet**, un petit comptoir qui délivre des tickets numérotés.
Deux images en sont déjà construites :

```text
guichet:1.0   respecte le contrat
guichet:0.9   un ancien build, qui ne le respecte pas
```

Écrivez **`/opt/dsoxlab-images-tester-le-contrat/tester-contrat.sh`**. Il prend
un nom d'image, lance cette image comme le ferait un utilisateur, puis rend :

```text
0         l'image respecte le contrat
non nul   elle ne le respecte pas, et la sortie dit quel contrôle l'a refusée
```

L'énoncé est aussi déposé dans
`/opt/dsoxlab-images-tester-le-contrat/MISSION.md`.

## Ce qu'un utilisateur de l'image peut attendre

| Attente | Ce que cela veut dire pour le guichet |
| --- | --- |
| Elle démarre | elle répond à `GET /ouvert` par un 200 sur le port `8099`, atteint par un port publié |
| Elle fait son travail | `POST /ticket` répond 201 et délivre le numéro suivant, `GET /tickets` rend le nombre de tickets délivrés |
| Elle se configure | sans `GUICHET_SITE` elle s'arrête aussitôt, avec un code non nul et un message qui nomme la variable ; avec elle, `/ouvert` mentionne le site |
| Elle n'exige aucun privilège | le processus n'est pas root, et le service tourne encore quand le conteneur est lancé avec un système de fichiers en lecture seule, son dossier de données `/var/lib/guichet` étant le seul endroit inscriptible |
| Elle s'arrête quand on le demande | `docker stop` la termine bien avant le délai de grâce de dix secondes, avec le code 0 ou 143, et le compteur est toujours là quand on remonte le même dossier de données |

## Ce qui est noté

Votre **script**, joué par les contrôles contre un jeu d'images. L'une respecte
le contrat et doit être acceptée. Les autres sont cassées de manières
différentes, vous ne les avez pas toutes vues : chacune doit être refusée par
un code non nul.

Un script qui rend toujours 0 accepte toutes les images cassées. Un script qui
rend toujours 1 refuse aussi la bonne, et aucun de ses refus ne compte alors.
Seul un script qui les distingue est noté.

Ce que le script crée, il le retire : conteneurs et volumes. Un test qui laisse
ses débris derrière lui empoisonne le suivant.

Le langage est libre, du moment que `bash tester-contrat.sh <image>` le lance.
Ne modifiez pas la configuration du démon, et ne supprimez pas `guichet:1.0` :
les contrôles construisent leurs propres images à partir d'elle.
