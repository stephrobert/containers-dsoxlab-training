# reseau-publication-de-ports : trois postures, un seul défaut

## Ce que ce lab éprouve

Que publier un port est un choix à **trois** branches, et que son défaut est le
plus ouvert des trois. `-p 8080:80` publie sur toutes les interfaces, parce que
l'adresse de publication est optionnelle. C'est le geste le plus banal de
Docker, et celui qui expose un service sans qu'on l'ait décidé.

## Les trois postures, mesurées avant d'être écrites

Sur `docker.lab`, le 2026-10-30 :

| Publication | depuis `127.0.0.1` | depuis l'adresse routable |
| --- | --- | --- |
| `-p 127.0.0.1:P:80` | joint | **ne joint pas** |
| `-p <routable>:P:80` | **ne joint pas** | joint |
| aucune | ne joint pas | ne joint pas |

Les trois lignes sont le lab. Chacune correspond à un besoin réel, et chacune
se trompe différemment.

## Le piège qui invaliderait tous ces contrôles

Le proxy de Docker **accepte une connexion avant que quoi que ce soit
n'écoute**. Vérifié ici le 2026-10-30, sur un `-p 127.0.0.1:18099:1234` dont le
conteneur n'écoutait nulle part : la connexion aboutissait.

Les contrôles lisent donc la **réponse**, jamais la seule connexion. Un test qui
se contenterait d'un `connect()` réussi déclarerait joignable un service absent,
et ce lab noterait exactement l'inverse de ce qu'il mesure.

C'est aussi pour cela que l'écouteur répond un jeton plutôt que de simplement
exister : une réponse lisible est la seule preuve qu'un service sert.

## Pourquoi chaque posture est mesurée deux fois

Les contrôles lisent ce que le moteur **déclare** publier, puis éprouvent ce
que la machine **fait**.

Les deux peuvent diverger : une règle de pare-feu, un second conteneur publié
sur le même port, un écouteur qui n'a pas redémarré. Un lab qui ne lirait que
la déclaration validerait un conteneur recréé sans son service.

## Pourquoi une image plutôt qu'une commande

Changer la publication d'un conteneur exige de le **recréer** : `-p` ne se
modifie pas à chaud, et c'est une leçon du lab.

L'apprenant doit donc pouvoir relancer l'écouteur sans le réécrire, d'où
l'image qui le porte en `CMD`. Un lab qui aurait passé l'écouteur en ligne de
commande aurait obligé l'apprenant à deviner une commande qu'il n'a jamais vue,
ce qui n'a rien à voir avec le sujet.

## Aucune adresse n'est écrite en dur

Ni dans les tests, ni dans la solution, ni dans le setup. L'adresse routable
est déduite de la route par défaut, au moment de la notation.

Un test qui porterait `10.10.120.11` serait faux sur une machine adressée
autrement, et le lab mourrait au premier changement de réseau. Le setup la
dépose en revanche dans l'énoncé, puisque l'apprenant doit l'écrire dans son
`-p`.

## Deux assertions indissociables, et pourquoi elles ne font qu'un contrôle

Le quatrième contrôle exige que `interne` ne publie rien **et** qu'il reste
joignable par `vitrine`.

Les deux ne se séparent pas : ne rien publier est trivial en détruisant le
conteneur. Un contrôle qu'on satisfait en retirant le sujet ne mesure rien,
donc la joignabilité interne est la contrepartie obligatoire.

## L'état de départ est cassé, et c'est la règle du dépôt

| Conteneur | État de départ | Geste attendu |
| --- | --- | --- |
| `vitrine` | `0.0.0.0:18080` | republier sur `127.0.0.1` seul |
| `annexe` | ne publie rien | publier sur la seule adresse routable |
| `interne` | `0.0.0.0:18082` | ne plus rien publier |

Aucune des trois fautes n'est un accident : chacune est l'erreur qu'on commet
par défaut. Une tâche du setup **vérifie** cet état avant de rendre la main.

## Ce que le lab n'exige pas

Un chemin. Les conteneurs se recréent en ligne de commande comme par l'API ou
par un fichier Compose. Seul l'état compte, et il est mesuré sur le moteur et
sur le réseau.
