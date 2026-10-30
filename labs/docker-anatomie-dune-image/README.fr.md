# docker-anatomie-dune-image : couches, partage, configuration

## Ce que ce lab éprouve

Qu'une image est un **empilement** de couches, que ces couches se **partagent**
entre images, et qu'elle porte en plus une **configuration** qui n'est pas son
contenu. Le lab précédent interrogeait un conteneur en marche ; celui-ci
interroge une image au repos.

## Le piège est mesuré, pas supposé

`greffe:1.0` porte **cinq** couches, pour trois instructions qui semblent en
créer une chacune (deux `RUN` et un `COPY`), plus la base. La cinquième vient
de `WORKDIR`, qui crée le répertoire quand il n'existe pas.

Relevé sur `docker.lab` le 2026-10-30. C'est ce qui rend le lab utile : lire le
Dockerfile ne suffit pas, et un apprenant qui compte les instructions se trompe
de une. Le message du contrôle le lui **dit**, plutôt que de le laisser
recompter en boucle.

## Pourquoi deux images, et pourquoi leurs premières lignes sont identiques

Le partage de couches n'a lieu que si l'instruction qui les produit est
identique, dans le même ordre, sur le même contexte. Les deux Dockerfile
partagent donc leurs trois premières lignes **au caractère près**, et le même
fichier de contexte.

C'est fragile par nature, et c'est le sujet : la moindre différence, même un
espace, produirait deux jeux de couches distincts et doublerait la place
occupée. Une tâche du setup vérifie que le partage a bien lieu avant de rendre
la main.

## Les deux sens du partage, et pourquoi ce ne sont pas deux fois la même question

| Contrôle | Ce qu'il mesure | Ce qu'il enseigne |
| --- | --- | --- |
| `partagees` | les couches communes aux deux | pourquoi dix images d'un socle ne pèsent pas dix socles |
| `propres` | celles que `2.0` a en plus | ce que coûte réellement une variante |

Le premier justifie une architecture, le second chiffre une décision. C'est le
même ensemble regardé des deux côtés, et les deux chiffres servent dans des
conversations différentes.

## La révision : une valeur qui n'est nulle part

Elle est posée **en ligne de commande** à la construction, avec `--label`. Donc
elle n'est dans aucun Dockerfile de la machine, que l'apprenant peut lire. Et
elle n'apparaît **pas** dans l'historique de l'image, ce qui a été vérifié sur
la machine plutôt que supposé.

Elle n'existe que dans `.Config.Labels`, et elle est tirée au hasard à chaque
`run`. C'est la seule des quatre réponses qu'on ne peut ni déduire, ni recopier.

## Une honnêteté sur la répétabilité

Les trois premières réponses **ne changent pas** d'un passage à l'autre : elles
décrivent une construction fixe. Un apprenant qui a déjà joué le lab pourrait
les recopier.

C'est assumé. Le lab n'est pas un jeu de devinettes, et recopier les trois
nombres suppose de les avoir trouvés une première fois. La quatrième réponse,
elle, interdit de rejouer le lab de mémoire.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | quatre clés, quatre valeurs **vides** | les renseigner | 1 à 4 |

## Ce que le cleanup doit impérativement retirer

Les **images**, pas seulement leurs tags. Une image conservée garderait la
révision du passage précédent, et le prochain `run` reconstruirait par-dessus :
le contrôle de la révision deviendrait vrai sans travail, puisque la réponse
d'hier serait encore valable aujourd'hui.

## Ce que le lab n'exige pas

Un chemin. `docker image inspect`, `docker history` et `docker image ls --tree`
mènent au même compte de couches. La révision se lit par un champ précis comme
dans la sortie complète de l'inspection.
