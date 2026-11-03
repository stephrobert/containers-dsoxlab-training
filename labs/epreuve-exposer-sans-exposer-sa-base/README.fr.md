# epreuve-exposer-sans-exposer-sa-base : l'épreuve du module « Exposer et relier »

## Ce que cette épreuve éprouve

Exposer une application sans exposer ce qu'elle détient. Elle clôt les leçons
du module et ne réexplique rien : ce qu'il faut savoir y a été enseigné,
celle-ci le mesure.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## Pourquoi elle a été recentrée

Elle redisait le lab d'une leçon antérieure : quatre de ses cinq contrôles
portaient sur la résolution de noms, pendant que le troisième enseignement du
module, l'**isolement**, n'était mesuré nulle part dans le catalogue.

Une épreuve de fin de module note la **combinaison** de ce que le module
enseigne, pas ce qu'une leçon d'avant a déjà prouvé.

## Les trois enseignements, et la combinaison

| Contrôle | Ce qu'il mesure |
| --- | --- |
| le frontal ne publie que sur l'interface demandée | une publication se lie à une **adresse** autant qu'à un port |
| la base répond à un **alias** distinct de son nom | un nom de service survit au remplacement du conteneur, un renommage non |
| la base est sur un réseau **sans issue** | ce qui y vit résout les noms et ne sort plus |
| la base ne publie aucun port | **l'exigence critique** |
| la requête métier aboutit **malgré** l'isolement | la combinaison, et c'est pour elle que l'épreuve existe |

Les deux premières exigences se contrarient avec la troisième : isoler la base
la coupe de tout, publier le frontal demande au contraire une issue. Les tenir
ensemble demande de poser le frontal sur les **deux** réseaux, ce qu'aucun
contrôle ne dit.

## Comment l'isolement est prouvé, et pourquoi pas autrement

Deux faits, et le second seul fait preuve. Tous les réseaux de la base sont
déclarés **internes**, et surtout la base **n'a aucune route par défaut**, ce
qui se lit dans le conteneur.

On ne tente **pas** une connexion vers l'extérieur. Mesuré le 2026-11-02 : un
conteneur sur un réseau interne n'a aucune route par défaut, là où un conteneur
ordinaire en a une. Une tentative de connexion, elle, passerait au vert sur une
machine privée d'accès sortant, donc pour la mauvaise raison, et le resterait le
jour où l'isolement disparaîtrait.

Mesuré aussi, et sans quoi l'épreuve serait injouable : un conteneur rattaché
aux **deux** réseaux garde sa route par défaut **et** résout l'alias.

## L'exigence critique

**Un port publié sur l'inventaire fait échouer l'épreuve**, même à 80 points.
Une base joignable depuis le réseau de l'entreprise est le défaut que cette
épreuve existe pour éliminer : le compenser par de bons points ailleurs
reviendrait à délivrer une attestation sur une installation exposée.

Elle porte sur **ce seul fait**. Elle en mêlait deux, le port publié et le
réseau d'attache, si bien qu'un apprenant qui ratait le réseau perdait son
exigence critique pour une raison qui n'est pas celle que l'énoncé annonce.

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

Le nom des réseaux, et le chemin suivi. Elle note l'état final. Un apprenant
qui nomme ses réseaux autrement, ou qui s'y prend en plusieurs gestes, a réglé
la panne.

## Après l'épreuve

`dsoxlab clean` retire tout ce que le lab a posé, **y compris les réseaux que
vous avez créés** : ils sont retrouvés par les conteneurs du lab qui y sont
attachés, puisque l'épreuve n'impose aucun nom. Le réseau par défaut du moteur
n'est jamais touché.
