# Les quatre labs que l'audit du 2026-11-01 a nommés

> **ÉCRITS LE 2026-11-02, les quatre.** Ce document reste comme cahier des
> charges : il dit ce que chaque lab devait prouver, et c'est à lui qu'on
> revient pour juger si un test dérive de son intention. L'état réel des labs se
> lit dans `validation-labs.json`, jamais ici.
>
> | lab | ce qu'il note | seuil |
> | --- | --- | --- |
> | `epreuve-livrer-une-image` | 4 contrôles, deux hôtes | 75 % |
> | `epreuve-restaurer-une-stack` | 4 contrôles, deux hôtes | 75 % |
> | `compose-retour-arriere` | 4 contrôles | sans seuil |
> | `compose-profils-et-variantes` | 4 contrôles | sans seuil |

L'audit du plan de formation a conclu « non, pas encore une formation de
référence », et quatre de ses douze points demandent un lab neuf. Les voici,
avec ce que chacun doit **prouver**, et pourquoi il n'existe pas déjà.

Le reste du plan vit dans le dépôt du site :
`todo/plan-formation-docker/PLAN-FORMATION-DOCKER.md`.

## 1. `epreuve-livrer-une-image` : l'épreuve du niveau 2 (C22)

**Pourquoi il manque.** La compétence c22 est « livrer une image qu'un client
vierge récupère et exécute, avec un accès registre limité, une identité
vérifiée, des tests au runtime, et aucun secret intégré ». Le contrat
`conteneurs-22` n'atteignait VALIDE qu'en citant sept labs existants, ce que la
règle E interdit (aucun lab cité deux fois). `registry-droits-minimaux` couvre
l'ACL et le tirage par digest depuis une seconde VM, mais ni « image testée »
ni « aucun secret intégré ».

**Ce que le lab doit prouver**, et chaque point est un test :

- l'image est construite puis **publiée** sur le registre local du lab ;
- un **client vierge** (`docker-client.lab`) la tire **par digest**, avec des
  identifiants qui n'ont que le droit de lecture ;
- l'image **répond** une fois lancée sur ce client : un test au runtime, pas un
  `docker inspect` ;
- **aucun secret n'est dans l'image** : ni dans une couche, ni dans
  `docker history`, ni dans la configuration. Le secret du build existe et sert
  (il faut bien tirer une dépendance privée), mais il ne survit pas ;
- le compte de lecture **ne peut pas pousser** : la tentative échoue, et le test
  le vérifie plutôt que de l'affirmer.

**Niveau** c2, `lab_type: challenge`, `exam_passing_score` obligatoire (c'est
une épreuve, et sans seuil `dsoxlab submit` ne rend aucun verdict).
**Deux hôtes** : `docker.lab` et `docker-client.lab`, tous deux déjà dans
`meta.yml`.

## 2. `epreuve-restaurer-une-stack` : l'épreuve du niveau 3 (C34)

**Pourquoi il manque.** `epreuve-remettre-une-stack-en-service` prouve « livrer une stack
exploitable » au minimum, en **un seul test**, sur un couple `writer`/`web` qui
sert un fichier texte. Il ne prouve ni la restauration après perte, ni le
passage sur un environnement distinct, qui sont les critères du niveau. Il
devient un lab d'entraînement de C26.

**Ce que le lab doit prouver :**

- la stack **fonctionne** : une requête métier traverse le frontal, l'API et la
  base, et rend une donnée écrite par l'apprenant ;
- une **panne est injectée** par le setup, sans être annoncée dans l'énoncé
  autrement que par ses symptômes ;
- la **restauration** ramène le service **et les données** : une donnée écrite
  avant la panne est présente après, et c'est un **témoin** que l'énoncé
  interdit de recréer à la main ;
- la restauration se fait sur un **environnement distinct** (`docker-client.lab`),
  pas sur l'hôte d'origine ;
- les protections ne sont pas retirées pour faire passer le test : le réseau de
  données reste interne, et un test le vérifie après la restauration.

**Niveau** c3, `lab_type: capstone`, `exam_passing_score` obligatoire.
**Deux hôtes.** C'est le lab qui doit porter le **fil rouge** (voir plus bas).

## 3. `compose-retour-arriere` : la compétence c33, aujourd'hui examinée sans être enseignée

**Pourquoi il manque, et c'est le trou le plus grave.** La compétence c33 est
« déployer une version et choisir un retour arrière compatible avec les
données ». Le seul endroit du catalogue où le rollback est mesuré est
`rollback.sh` de `capstone-chaine-complete`, c'est-à-dire **l'épreuve finale** :
la formation examine en finale une compétence qu'elle n'a jamais entraînée.

**Ce que le lab doit prouver :**

- une **nouvelle version** de l'image est déployée par son digest, et le service
  répond ;
- un **retour arrière compatible** ramène la version précédente **sans perte** :
  la donnée écrite sous la nouvelle version est toujours là ;
- un **retour arrière incompatible est refusé**, et c'est le cœur du lab : la
  nouvelle version a migré le schéma de façon irréversible, l'ancienne ne sait
  plus le lire, et l'apprenant doit le **constater puis l'expliquer**, pas le
  contourner. Le test vérifie que l'ancienne version n'a pas été lancée sur le
  schéma migré, ou qu'elle l'a été et a échoué proprement ;
- le **témoin** : une donnée métier écrite avant la migration, qu'il est
  interdit de recréer.

**Niveau** c3, `lab_type: lab`. Un hôte suffit.

## 4. `compose-profils-et-variantes` : la compétence c30

**Pourquoi il manque.** c30 est « produire deux configurations distinctes sans
outil de développement en déploiement ». `compose-plusieurs-environnements`
couvre la fusion par deux fichiers et la promotion d'une image, mais ni les
**profils**, ni `watch`, ni le contrôle qu'aucun montage de source ne survit en
déploiement. Ce dernier point est le défaut réel du terrain : un bind mount de
développement laissé en production.

**Ce que le lab doit prouver :**

- la variante de **développement** monte les sources et expose un port de
  débogage, et le service recharge au changement ;
- la variante de **déploiement**, obtenue du même fichier de base, **ne porte
  aucun** montage de source ni port de débogage : le test lit la configuration
  **effective** (`docker compose config`) et l'état réel des conteneurs, pas le
  fichier d'entrée ;
- un service **optionnel** (profil) ne démarre pas sans son profil, et démarre
  avec ;
- la bascule entre les deux variantes ne demande **aucune édition** du fichier
  de base.

**Niveau** c3, `lab_type: lab`. Un hôte suffit.

## Le fil rouge : à porter, pas à promettre

`projet.pedagogie.fil_rouge` du parcours promet « API et PostgreSQL avec frontal
HTTP », et le `meta.yml` de ce catalogue écrit « One and the same FastAPI
application runs through the whole path ». Mesuré le 2026-11-01 sur les 77
labs : **FastAPI ou uvicorn apparaît dans zéro lab**, PostgreSQL dans trois, un
frontal dans deux.

Les labs 2, 3 et 4 ci-dessus sont ceux qui peuvent le porter : API, base et
frontal, le même code d'un lab à l'autre. S'ils le portent, la promesse devient
vraie pour trois épreuves sur quatre. S'ils ne le portent pas, la promesse doit
être **retirée** du parcours et du `meta.yml` : une formation de référence ne
promet pas un fil rouge qu'elle n'a pas.
