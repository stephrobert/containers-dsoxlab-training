# epreuve-reconstruire-une-image-pour-deux-architectures : l'épreuve d'enchaînement

## Ce que cette épreuve éprouve

Qu'une **seule** image réunisse quatre exigences qui ont été vues séparément.
Elle clôt le module « Industrialiser la chaîne des images » et ne réexplique
rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## Son recouvrement est assumé, et c'est ce qui la justifie

Quatre labs d'entraînement mesurent déjà ses gestes, et deux sont eux-mêmes des
épreuves :

| Geste | Déjà mesuré par |
| --- | --- |
| index à deux plateformes, les deux s'exécutent, digest de l'index | `images-multi-architecture`, déjà challenge |
| secret absent des couches et de l'historique | `buildkit-secret-de-build`, déjà challenge |
| multi-étapes | `images-build-multi-etapes` |
| taille | `images-optimiser-la-taille` |

Le recouvrement a été relevé et porté à l'arbitrage avant l'écriture, puis
assumé le 2026-11-02. La raison est que **aucun des quatre ne mesure
l'enchaînement**. Or c'est l'enchaînement qui compte en production : une image
légère dont le secret a fui ne vaut rien, et une image propre qui ne sert qu'une
architecture ne se déploie pas.

## Ce que le banc a établi avant l'écriture

Quatre points étaient incertains, et chacun pouvait rendre l'épreuve
inécrivable. Tous ont été mesurés le 2026-11-02 :

- **`--build-arg` laisse le jeton dans l'historique** : deux occurrences. C'est
  le défaut livré, et il est réel ;
- **`--mount=type=secret` n'en laisse aucune**, ni dans l'historique ni dans les
  couches, et la dépendance est bien produite. C'est la correction, et elle est
  mesurable ;
- `buildx` pousse un index OCI, et **les deux architectures s'exécutent par
  émulation** sur cette VM amd64 ;
- **l'index porte quatre manifestes et non deux** : `buildx` y ajoute ses
  attestations de provenance, qui se présentent comme des plateformes `unknown`.

Le dernier point a changé le contrôle : il cherche `amd64` et `arm64` **parmi**
les manifestes, au lieu d'en exiger exactement deux. Un contrôle qui compterait
les entrées refuserait le résultat normal de l'outil.

## Pourquoi les contrôles portent sur l'image tirée du registre

Parce que `buildx` avec une sortie de type registre **ne laisse rien en local**.
Exiger une image locale punirait la façon normale de publier, et l'épreuve note
l'état final.

C'est aussi plus juste : on mesure ce qui est **livré**, pas ce qui est resté sur
le poste de celui qui a construit.

## Pourquoi la dépendance privée est le condensat du jeton

Un vrai dépôt privé demanderait un service réseau de plus, et le banc a montré
qu'un `RUN` de build peut le joindre par son adresse de bridge. Mais ce qui est
**mesuré** ne changerait pas d'un iota : que le secret ait **servi**, et qu'il
n'ait pas **fui**.

Le condensat prouve les deux sans ajouter de pièce, et l'énoncé le dit
franchement plutôt que de faire semblant. Un lab qui simule doit dire qu'il
simule.

## L'exigence critique, et pourquoi c'est la fuite la plus discrète du métier

**Le jeton lisible dans l'historique fait échouer l'épreuve**, même à 80 points.

Elle est discrète parce que l'image elle-même ne contient rien de suspect : on
peut l'inspecter, lister ses fichiers, lancer un shell dedans, et ne rien voir.
La valeur est dans les métadonnées de construction, que `docker history
--no-trunc` affiche et que personne ne regarde.

## Ce que ce lab rend à la machine

Tout ce qu'il a posé, et deux pièces méritent une mention :

- **le constructeur buildx**, qui est un conteneur portant le cache de build de
  toutes les plateformes. Le laisser occuperait plusieurs centaines de
  mégaoctets ;
- **l'émulation n'est PAS retirée**, et c'est délibéré. Elle vient de paquets
  Debian et d'une unité systemd, pas d'un objet du moteur : la désinstaller
  toucherait la machine plus profondément que le lab ne l'a fait, et
  `images-multi-architecture` en a besoin aussi.
