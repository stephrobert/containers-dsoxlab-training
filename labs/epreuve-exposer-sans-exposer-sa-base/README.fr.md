# epreuve-exposer-sans-exposer-sa-base : l'épreuve du module « Exposer et relier »

## Ce que cette épreuve éprouve

Faire se parler deux conteneurs par leurs noms, et n'ouvrir vers l'extérieur
que ce qui doit l'être. Elle clôt les leçons du module et ne réexplique rien :
ce qu'il faut savoir y a été enseigné, celle-ci le mesure.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## La panne posée, et elle n'est dite nulle part dans l'énoncé

| Faute | Symptôme visible | Ce qu'elle enseigne |
| --- | --- | --- |
| les deux conteneurs sur le réseau **par défaut** | aucun nom ne résout, alors que les adresses se joignent | le réseau par défaut donne une route, pas un résolveur |
| la vitrine interroge `stock`, que personne ne porte | le nom attendu ne résout pas, même sur un réseau à soi | les alias réseau existent pour ça |
| `inventaire` publie un port sur toutes les interfaces | l'audit le signale | rien ne retire un `-p` sur un conteneur existant |
| `vitrine` publie sur toutes les interfaces | l'audit le signale aussi | une publication se lie à une adresse, pas seulement à un port |

Les quatre sont indépendantes, et ce sont exactement celles que l'on commet en
lançant deux conteneurs à la main sans penser au réseau. La première est la plus
instructive : « ça marche » par adresse IP, donc on ne soupçonne pas le réseau.

## Quatre symptômes, deux gestes

Créer un réseau à soi, puis recréer les deux conteneurs dessus : l'un avec son
alias et sans publication, l'autre publié sur la seule interface demandée.
**Deux gestes règlent les quatre fautes**, et c'est ce qui fait la valeur de
l'épreuve : le diagnostic précède la main.

Corriger faute par faute fonctionne aussi, en quatre fois. Les tests notent
l'état final, donc les deux chemins valent la même note.

## Pourquoi le nom réel est exigé en plus du nom cherché

Sans cette exigence, renommer le conteneur en `stock` satisferait les autres
contrôles, et l'apprenant n'aurait rien appris des alias. Elle est **annoncée
dans l'énoncé**, donc ce n'est pas un piège, et elle décrit la situation réelle :
l'application a son nom à elle, écrit dans une configuration qu'on ne peut pas
changer, et l'exploitation garde le sien, celui des journaux et des inventaires.

Mesuré dans ce dépôt : un alias posé sur un réseau laisse le vrai nom résoudre.
Les deux exigences sont donc satisfiables ensemble, et seul un renommage les
oppose.

## L'exigence critique

**Un port publié sur l'inventaire fait échouer l'épreuve**, même à 80 points.
Une base joignable depuis le réseau de l'entreprise est le défaut que cette
épreuve existe pour éliminer : le compenser par de bons points ailleurs
reviendrait à délivrer une attestation sur une installation exposée.

## Où vit la donnée témoin, et pourquoi dans l'image

La valeur que seul l'inventaire détient est portée par un **label de l'image**,
pas par un fichier de l'hôte ni par un volume. Deux raisons :

- l'épreuve demande de **recréer** les conteneurs, et une donnée portée par
  l'image survit à leur recréation : le contrôle de la traversée ne punit donc
  pas la bonne façon de s'y prendre ;
- les volumes ne sont pas au programme de ce module. Les introduire ici
  ajouterait une notion que l'apprenant n'a pas vue.

Elle est **tirée au sort à chaque passage** : un chiffre figé dans un dépôt
public est une réponse publiée.

## Ce que l'épreuve ne mesure pas

Le nom du réseau, et le chemin suivi. Elle note l'état final. Un apprenant qui
nomme son réseau autrement, ou qui s'y prend en quatre gestes, a réglé la panne.

## Après l'épreuve

`dsoxlab clean` retire tout ce que le lab a posé, **y compris le réseau que vous
avez créé** : il est retrouvé par les conteneurs du lab qui y sont attachés,
puisque l'épreuve n'impose aucun nom. Le réseau par défaut du moteur n'est
jamais touché.
