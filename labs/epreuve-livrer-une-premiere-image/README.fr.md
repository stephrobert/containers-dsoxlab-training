# epreuve-livrer-une-premiere-image : l'épreuve du module de construction

## Ce que cette épreuve éprouve

Écrire un Dockerfile qui livre une image qu'on peut publier sans rougir. Elle
clôt le module « Construire et publier une image » et ne réexplique rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## Ce que le dépôt contient, et pourquoi chaque pièce y est

| Pièce | Doit-elle entrer dans l'image ? | Ce qu'elle mesure |
| --- | --- | --- |
| `app.sh` | oui | sans elle, l'image ne répond rien |
| `donnees/reference` | oui | une image qui démarre sans ses données répond son propre code d'erreur |
| `.identifiants` | **non** | l'exigence critique : un secret livré est un secret publié |
| `travail/`, 40 Mo | **non** | le seuil de taille le voit, et c'est la façon mesurée de le prouver |

Les quarante mégaoctets sont tirés de `/dev/urandom`, donc **incompressibles** :
une image qui embarquerait des zéros se compresserait, et le contrôle de taille
ne mesurerait plus rien.

## Pourquoi le seuil de taille est mesuré, et non écrit

Le `run` construit une image de **référence** avec un Dockerfile correct,
relève sa taille réelle sur cette machine, supprime l'image, et consigne le
seuil. Le Dockerfile de référence vit dans `/root` et est effacé juste après :
il porte la réponse.

Une taille écrite en dur dans le test périmerait à la première mise à jour de
l'image de base, et le lab se mettrait alors à **refuser du travail juste**.
C'est le genre de défaut qui fait douter de la machine quand c'est le lab qui se
trompe.

## L'exigence critique, et pourquoi elle se mesure dans l'archive

**Le jeton présent dans une couche fait échouer l'épreuve**, même à 80 points.

Le contrôle lit `docker save`, pas le conteneur. La raison est précise : un
`RUN rm` qui efface un secret à l'étape suivante laisse **intacte la couche qui
le portait**. Le fichier a disparu de la vue finale, et il voyage toujours avec
l'image. Un contrôle qui regarderait dans le conteneur ne verrait rien, et
déclarerait propre une image qui ne l'est pas : il mesurerait la vue, pas le
contenu.

Et c'est la **valeur** du jeton qui est cherchée, non le nom du fichier :
renommer ne change rien au fait que le secret voyage.

## Pourquoi l'UID doit être numérique

Un nom d'utilisateur ne se résout que dans l'image qui le définit : il vit dans
son `/etc/passwd`, qu'un orchestrateur ne lit pas et qu'un contrôle d'admission
ne peut pas vérifier. L'UID numérique est la seule forme qu'un tiers peut
exiger, et c'est celle que réclament les politiques qui refusent
`runAsUser: 0`.

Le chiffre, lui, est libre : ce qui est mesuré n'est pas sa valeur.

## Elle ne double pas `epreuve-livrer-une-image`

Celle-là clôt un module plus tardif : elle mesure une livraison vers un **client
nu**, sur deux machines, avec un compte en lecture seule. Celle-ci mesure la
**première** livraison, sur une seule machine.

Les deux partagent une exigence, le secret absent des couches, et c'est
délibéré : c'est la faute la plus coûteuse du métier, et elle se mesure à chaque
fois qu'on construit, pas une fois dans un parcours.

## Ce que l'épreuve ne mesure pas

La construction multi-architecture, les étapes multiples, l'optimisation fine de
la taille. Ce sont les sujets d'épreuves plus tardives.
