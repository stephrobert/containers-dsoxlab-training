# docker-verifier-son-moteur : quatre réponses, pas une

## Ce que ce lab éprouve

Qu'« installé » et « utilisable » sont deux états distincts, et que le second se
vérifie sur quatre plans qui ne se réparent pas du même geste. C'est le premier
lab du catalogue, et volontairement : avant de lancer un conteneur, savoir si
le moteur peut en lancer un.

Il est noté sur l'**état de la machine**, jamais sur les commandes tapées.
`systemctl enable --now`, une réparation à la main du lien d'unité, `usermod
-aG` ou `gpasswd -a` mènent aux mêmes états, et noter la commande noterait un
style.

## Pourquoi quatre contrôles et non un seul

Un `docker run` qui réussit prouverait les quatre d'un coup. C'est exactement
ce qu'il ne faut pas noter : il masquerait **lequel** manquait, et c'est la
seule information utile à qui dépanne.

Le cas qui justifie le découpage à lui seul est le deuxième : un service
démarré à la main passe tous les essais de la journée et disparaît au premier
redémarrage. Il n'y a aucune façon de distinguer cette machine d'une machine
saine, sauf en regardant l'activation au démarrage séparément.

## L'état de départ est cassé, et c'est la règle du dépôt

Un test doit porter sur ce que l'état de départ ne porte PAS. Un setup qui
installerait et démarrerait Docker rendrait deux contrôles verts avant tout
travail : le lab noterait son propre setup.

Le setup défait donc trois choses indépendantes :

| Défait | Contrôle qui le mesure |
| --- | --- |
| `docker.service` arrêté | 1, le moteur répond |
| `docker.service` et `docker.socket` désactivés | 2, la persistance |
| le compte retiré du groupe `docker` | 3, l'accès sans sudo |
| aucun conteneur laissé derrière | 4, une exécution réelle |

Le socket mérite une mention : sans l'arrêter **aussi**, systemd relancerait le
service à la première connexion, et le contrôle 1 passerait au vert sans que
l'apprenant ait rien fait.

## Deux pièges posés à dessein

**Les groupes sont lus à la connexion.** L'apprenant qui s'ajoute au groupe
`docker` puis réessaie aussitôt reçoit encore un refus, et croit avoir manqué
son geste. Le contrôle mesure l'appartenance déclarée, pas ce que la session
courante peut faire : le bon geste compte même si le terminal l'ignore encore.
L'énoncé le dit d'avance, parce que ce piège décourage plus qu'il n'enseigne.

**La commande qui ajoute un groupe peut remplacer les autres.** Un contrôle
vérifie donc que le compte garde `sudo`. Un apprenant qui le perd a fait le
geste de travers, et la machine devient inadministrable, ce qui est une panne
plus grave que celle qu'il réparait.

## Pourquoi deux contrôles passent par `sudo`

Pour que les quatre plans restent indépendants. Interroger le moteur avec le
compte de l'apprenant ferait échouer « le moteur répond » quand seul le groupe
manque : deux points perdus pour un geste oublié, et un message qui annonce un
démon muet alors qu'il répond. L'accès sans sudo a son contrôle, et lui seul le
mesure.

## Ce que le lab n'exige pas

Les deux unités activées. L'une des deux suffit : le socket qui lance le
service à la demande est une réponse défendable, et exiger les deux imposerait
un chemin.
