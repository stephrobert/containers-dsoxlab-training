# docker-inspecter-un-conteneur : interroger un conteneur en marche

## Ce que ce lab éprouve

Qu'un conteneur en marche **s'interroge**, et que chaque question a sa commande.
Le lab précédent enseignait les états ; celui-ci enseigne ce qu'on peut savoir
d'un conteneur sans les changer : ce qu'il a dit, l'adresse qu'il a reçue, le
port par lequel on l'atteint, et ce qu'il a écrit depuis son démarrage.

## La décision qui tient tout le lab : le setup ne connaît aucune réponse

Les quatre valeurs sont produites **ailleurs que dans le dépôt** :

| Valeur | Qui la produit | Ce qui la rend |
| --- | --- | --- |
| le jeton de session | le conteneur, depuis `/dev/urandom` | ses journaux |
| la séquence de la trace | le conteneur, depuis `/dev/urandom` | le fichier, sorti du conteneur |
| l'adresse IP | le moteur, à la création | l'inspection du conteneur |
| le port de l'hôte | le moteur, parce que `-p 0:80` le lui laisse choisir | la table des ports |

Aucune ne transite par un fichier du dépôt, par la ligne de commande, ni par le
playbook. **Elles changent à chaque `run`.** Un apprenant ne peut donc pas les
trouver dans l'énoncé, ni recopier celles d'un passage précédent.

C'est ce qui sépare ce lab d'un questionnaire. Les tests recalculent chaque
réponse en interrogeant le moteur au moment de la notation, et confrontent ce
que l'apprenant **affirme** à ce que la machine **porte**.

## Pourquoi quatre sources disjointes

Une par commande du sujet : les journaux, l'inspection, la table des ports, la
copie d'un fichier.

La trace ne porte **pas** le jeton de session, et c'est voulu. Si elle le
portait, sortir le fichier donnerait la réponse de la première question, et
deux contrôles n'en mesureraient plus qu'un. C'est le genre de recouvrement qui
gonfle un barème sans rien mesurer de plus.

## Le piège construit, et il est honnête

Le port attendu est celui de **l'hôte**, pas le `80` du conteneur, qui est la
seule valeur que l'apprenant connaissait déjà en arrivant. Répondre `80` est la
faute de surface, et le message du contrôle la nomme explicitement plutôt que
de dire « mauvaise valeur ».

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | trois clés, trois valeurs **vides** | les renseigner | 1, 2 et 3 |
| `trace.log` dans le conteneur | absent de l'hôte | le sortir à l'identique | 4 |

Une tâche du setup **vérifie** cet état avant de rendre la main : le conteneur
tourne, il publie bien un port, et la trace n'est pas déjà sur l'hôte. Sans
elle, un passage mal nettoyé rendrait le lab déjà résolu avant d'être posé.

## Ce que le lab n'exige pas

Un chemin. `docker logs` et le fichier journal de l'hôte donnent le même jeton ;
`docker port`, `docker inspect` et `ss` donnent le même port ; `docker cp` et
une redirection de `docker exec` sortent le même fichier. Les trois chemins
comptent, et un apprenant qui atteint la bonne valeur autrement a appris la
même chose.

## Le seul geste qui coûte deux contrôles

Arrêter le conteneur pour le fouiller. Il perd alors son adresse et sa table
des ports, que le moteur ne conserve pas. Un helper dit cette cause **une fois
et clairement**, plutôt que de laisser deux contrôles refuser sur une valeur
vide : l'apprenant chercherait la faute dans sa réponse écrite, et elle n'y est
pas.
