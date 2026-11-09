# images-tester-le-contrat : écrire les tests qui refusent une image cassée

## Ce que ce lab éprouve

Que vous savez tester une image **de l'extérieur**, comme le font les gens qui la
font tourner, et que votre test distingue une image correcte d'images cassées de
natures différentes. Ce qui est noté n'est pas une image : c'est le script que
vous écrivez.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-11-09, avec Docker Engine 29.9.2 et un service construit
pour le lab. Une image correcte et huit images cassées, chacune ne différant de la
correcte que d'une ou deux lignes de Dockerfile, et ce qu'un script en voit :

| Image | Défaut | Ce que l'extérieur voit |
| --- | --- | --- |
| `guichet:1.0` | aucun | démarre, répond, compte, s'arrête en 0,5 s avec le code 0, garde son compteur |
| `guichet:0.9` | n'écoute que sur 127.0.0.1 | le conteneur est `Up`, rien ne répond par le port publié |
| dossier de données à root | l'utilisateur ne peut pas écrire | le conteneur s'arrête au démarrage, code 2 |
| erreur signalée, code de sortie 0 | la vérification est muette | `docker wait` rend 0 : pour un orchestrateur, un succès |
| aucune vérification de la variable | le service démarre sans elle | le conteneur tourne encore après 20 s |
| processus en root | trop de privilèges | `id -u` rend 0, le service répond normalement |
| écrit hors de son dossier de données | marche tant que le système de fichiers est inscriptible | le conteneur s'arrête au démarrage sous `--read-only` |
| ignore SIGTERM | `docker stop` ne l'arrête pas | code 137 au bout de 10,2 s |
| s'arrête proprement, écrit un compteur faux | données perdues | code 0 en une fraction de seconde, compteur revenu à 0 |

L'image correcte est la seule qu'aucun contrôle ne refuse. Chacune des autres est
refusée par **un** contrôle, et un seul : c'est ce qui permet à un script partiel
d'obtenir une note partielle.

## Pourquoi un jeu d'images, et pas une seule

Un script qui rend toujours 0 accepte toutes les images cassées. Un script qui
rend toujours 1 refuse aussi la correcte. Une seule image ne distingue ni l'un ni
l'autre d'un vrai test. Le jeu mêle une image correcte et des images cassées de
natures différentes, et les contrôles jouent votre script contre toutes.

## Pourquoi les refus ne comptent que si l'image correcte est acceptée

Un script absent rend un code non nul. Un script qui refuse tout aussi. Les deux
« refusent » les images cassées sans rien mesurer. Chaque contrôle de refus exige
donc d'abord que votre script accepte l'image correcte : sans cela, le refus ne
prouve rien, et le contrôle le dit au lieu de le créditer.

## Pourquoi la plupart des images ne sont pas là avant la notation

Seules `guichet:1.0` et `guichet:0.9` existent après le setup, parce que l'énoncé
les nomme. Les autres sont construites par les contrôles, au moment de noter, à
partir de l'image correcte, puis retirées. Un script écrit pour reconnaître les
images par leur nom passerait les deux premiers contrôles et échouerait aux
autres.

## Ce que le lab n'exige pas

La formulation de vos messages, l'ordre de vos contrôles, le langage du script
du moment que `bash tester-contrat.sh <image>` le lance, et une valeur de délai
particulière.

## L'état de départ est la règle du dépôt

Le script n'existe pas, donc les six contrôles sont faux avant tout travail. Une
tâche du setup vérifie que les deux images existent et qu'aucun script n'est là.
