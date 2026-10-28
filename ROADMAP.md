# Backlog des labs

Établi le 2026-10-01 depuis la matrice de `COVERAGE.md`, **rangé sous les huit
modules de la formation le 2026-10-28**. Chaque ligne porte le `doc_url`
**ancré** sur la section que le lab éprouve.

## Rangé sous le parcours, et plus sous son propre découpage

Jusqu'au 2026-10-28, ce backlog se découpait en onze blocs `c1` à `c10` plus
Swarm, nés avant que la formation ne soit pilotée. Le programme cible de
`src/data/parcours/docker.yaml` en compte **huit**, regroupés en quatre
niveaux, et deux découpages coexistaient donc avec des noms assez proches pour
qu'on les croie équivalents : `c1 comprendre` voulait dire « manipuler un
conteneur », le module `comprendre` du parcours voulait dire « regarder sous le
capot ».

C'est le second catalogue tenu à la main que décrit la règle K du socle de
pilotage, et il se réconcilie dans un seul sens : **le catalogue s'aligne sur
le parcours**. Les titres ci-dessous sont donc les modules du programme cible,
et `meta.yml` porte leurs identifiants mot pour mot.

Ce reclassement a fait apparaître ce qu'aucune relecture ne montrait : le
module **`compose-exploitation`** ne recevait que **deux** labs du backlog, pour
quatre leçons annoncées (journaux et ressources, sauvegarde et restauration,
mise à jour et retour arrière, épreuve 3). Le trou n'était pas visible tant que
les labs de Compose vivaient dans un seul bloc de onze.

**Les 64 ancres de ce backlog sont vérifiées contre les pages publiées :**

```console
$ python3 scripts/verifier-ancres.py
69 doc_url à contrôler
64 ancre(s) juste(s), 0 fausse(s), 0 page(s) injoignable(s), 5 doc_url sans ancre
```

Et il a fallu ce contrôle : la première rédaction de ce fichier portait
**44 ancres fausses sur 64**. Celles issues de l'inventaire du blog étaient
justes, celles écrites de mémoire étaient inventées, et rien ne les
distinguait à la lecture : un fragment faux donne un lien qui répond 200 et
dépose le lecteur en haut d'un guide de mille lignes.

`validate-structure --check-urls` ne voit pas ce défaut : il contrôle la page,
pas le fragment. `scripts/verifier-ancres.py` est né de là.

**Ces ancres visent les pages publiées aujourd'hui, pas les pages cibles.** Le
programme du pilotage prévoit des leçons dont l'URL est encore `null` : quand
elles existeront, les `doc_url` concernés se repointeront, et la règle D du
socle impose alors de suivre la page qui héberge le bloc `<Lab>`. Ce travail
n'est pas fait ici.

Le préfixe d'URL commun, omis dans les tableaux pour qu'ils restent lisibles :

```text
https://www.stephane-robert.info/docs/conteneurs/
```

## Comment lire ce backlog

| Colonne | Ce qu'elle dit |
| --- | --- |
| **id** | identifiant dsoxlab, en français, `<compétence>-<sujet>` |
| **type** | `lab` guidé, `challenge` sans recette, `capstone` sans sujet annoncé |
| **val** | `f` fonctionnel, `s` sécurité, quand le second a un sens réel |
| **prér.** | labs supposés joués, pour les capstones et les challenges |

Un identifiant ne porte **pas de numéro** : un numéro date de l'ordre
d'écriture du catalogue, jamais de l'ordre de lecture de la formation, et les
deux divergent dès qu'une leçon bouge. L'ordre est porté par le parcours.

## Tous les labs tournent dans une VM, et il n'y a plus de colonne pour le dire

**Décision de Stéphane du 2026-10-28 : on ne force pas l'apprenant à installer
Docker sur son poste.** Le lab monte une Debian 13 jetable par
`dsoxlab provision`, y installe le moteur, et la détruit à la fin.

C'est la raison qui change, pas seulement la valeur. L'ancienne règle était
`sh` par défaut, au nom du §20 du brief : ne pas faire provisionner une machine
pour jouer le premier lab. Elle faisait payer ce confort par l'installation
d'un démon Docker sur la machine de travail de l'apprenant, c'est-à-dire par
un changement durable sur un poste qui ne nous appartient pas, pour une
formation qu'on quitte au bout de quelques heures. Une VM se jette ; un
`apt install docker.io` sur un portable de bureau reste.

**Et le catalogue était le seul à dire le contraire.** Les **46 contrats de TP**
de `src/data/parcours/docker.yaml` déclarent tous
`environnement.reference: vm_linux_jetable`, et `projet.laboratoire` annonçait
déjà « VM Linux jetable Debian 13 ». Cette décision ne retourne donc pas le
pilotage : elle y ramène le catalogue, qui avait gardé la règle de son brief
d'origine.

La colonne `rt` est retirée des tableaux : elle ne porterait plus qu'une seule
valeur, et une colonne muette est exactement le travers que `gen_catalog.py`
reproche à la sienne. Les **90** labs de ce fichier sont donc en `runtime: vm`.

### Ce qui exige une SECONDE machine, et reste à câbler

`meta.yml` ne déclare aujourd'hui qu'un hôte, `docker.lab`. Six contrats du
pilotage en demandent deux, et il faudra les ajouter avant d'écrire ces
labs :

| Contrat | Ce qu'il exige |
| --- | --- |
| `conteneurs-21`, `conteneurs-22`, `conteneurs-44` | deux environnements isolés (publier ici, récupérer là) |
| `conteneurs-32`, `conteneurs-34` | deux environnements isolés (sauvegarder, restaurer ailleurs) |
| `conteneurs-18` | deux architectures, ou un périmètre réduit déclaré |

Un hôte nouveau **s'ajoute en fin de liste** dans `infra.hosts` : l'adresse IP
et la MAC dérivent de la position (`cidrhost(cidr, idx + 11)`), et insérer au
milieu réattribue les adresses des suivants, ce que libvirt refuse en cours de
route.

Swarm reste à part, avec ses trois managers : c'est l'arbitrage de topologie
qui n'est pas rendu, et le périmètre de la formation l'envoie de toute façon
vers un parcours distinct.

---

## Niveau c1 : utiliser et comprendre les conteneurs

### `conteneurs-utilisation` : utiliser les conteneurs (14 labs)

| id | type | val | doc_url ancré |
| --- | --- | --- | --- |
| `docker-verifier-son-moteur` | lab | f | `moteurs-conteneurs/docker/installation/#vérification-de-linstallation` |
| `docker-premier-conteneur` | lab | f | `moteurs-conteneurs/docker/cli/#lancer-et-gérer-les-conteneurs-docker` |
| `docker-cycle-de-vie` | lab | f | `moteurs-conteneurs/docker/concepts/#cycle-de-vie-dun-conteneur` |
| `container-entrypoint-et-cmd` | lab | f | `moteurs-conteneurs/docker/execution-depannage/#le-cycle-de-vie-dun-conteneur` |
| `container-signaux-et-pid-1` | lab | f | `moteurs-conteneurs/docker/execution-depannage/#stop-vs-kill--quelle-différence-` |
| `docker-inspecter-un-conteneur` | lab | f | `moteurs-conteneurs/docker/execution-depannage/#les-commandes-indispensables` |
| `docker-anatomie-dune-image` | lab | f | `images-conteneurs/#comment-est-construite-une-image-de-conteneur-` |
| `reseau-bridge-par-defaut` | lab | f | `moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation` |
| `reseau-bridge-dedie` | lab | f | `moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation` |
| `reseau-publication-de-ports` | lab | f+s | `moteurs-conteneurs/docker/network/#bonnes-pratiques-réseau` |
| `reseau-interne` | lab | f+s | `moteurs-conteneurs/docker/network/#le-réseau-none--isolation-totale` |
| `reseau-diagnostic-dns` | challenge | f | `moteurs-conteneurs/docker/network/#dépannage-réseau-docker` |
| `donnees-volumes-et-montages` | lab | f | `moteurs-conteneurs/docker/volumes/#vue-densemble-des-types-de-volumes` |
| `donnees-permissions-uid-gid` | lab | f | `moteurs-conteneurs/docker/volumes/#les-volumes-standards` |

`docker-premier-conteneur` est le lab d'entrée du catalogue : il doit se jouer
en moins d'une minute, sans rien construire, sinon il décourage avant
d'enseigner.

Les quatre labs de réseau et les deux de données tiennent ici parce que le
module les enseigne sur **un** conteneur : publier un port sans exposer tout
l'hôte, conserver des données, monter des fichiers. Les réseaux d'une **stack**
sont une autre compétence, et ils sont dans `compose-application`.

### `conteneurs-isolation` : mesurer l'isolation et remettre en service (10 labs)

| id | type | val | prér. | doc_url ancré |
| --- | --- | --- | --- | --- |
| `internes-namespaces` | lab | f | - | `moteurs-conteneurs/docker/sous-le-capot/#namespaces--isoler-ce-que-le-conteneur-voit` |
| `internes-cgroups-v2` | lab | f | - | `moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise` |
| `internes-stockage-des-images` | lab | f | - | `moteurs-conteneurs/docker/sous-le-capot/` |
| `internes-chaine-dexecution` | lab | f | - | `moteurs-conteneurs/docker/sous-le-capot/#comment-ces-mécanismes-fonctionnent-ensemble` |
| `container-limite-cpu` | lab | f | - | `moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise` |
| `container-ulimits-et-shm` | lab | f | - | `moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise` |
| `troubleshoot-exit-127` | lab | f | - | `moteurs-conteneurs/docker/execution-depannage/#décoder-les-exit-codes` |
| `troubleshoot-conflit-de-port` | lab | f | - | `moteurs-conteneurs/docker/execution-depannage/#checklist-de-debug-réseau` |
| `troubleshoot-permission-refusee` | lab | f | `donnees-permissions-uid-gid` | `moteurs-conteneurs/docker/volumes/#les-volumes-standards` |
| `troubleshoot-boucle-de-redemarrage` | lab | f | - | `moteurs-conteneurs/docker/execution-depannage/#restart-policies--redémarrer-automatiquement` |

`internes-stockage-des-images` a une raison d'exister que l'audit a trouvée :
sur le poste de mesure, la même image pesait **83 Mio par l'API et 329 Mio par
`docker images`**, parce que le moteur y employait le containerd image store.
Le lab fait constater l'écart et dire lequel des deux chiffres répond à quelle
question. **À rejouer dans la VM avant de l'écrire** : le moteur installé par
le lab n'emploie pas forcément ce magasin, et un lab qui enseigne un écart doit
d'abord constater que l'écart existe là où l'apprenant le jouera.

Les quatre `troubleshoot` préparent l'**épreuve 1** du niveau, qui demande de
remettre un conteneur en service : un symptôme, et rien qui nomme la cause. Les
incidents qui touchent l'hôte, eux, sont au niveau c4.

---

## Niveau c2 : construire et distribuer ses images

### `images-construction` : construire ses images (11 labs)

| id | type | val | doc_url ancré |
| --- | --- | --- | --- |
| **`images-identifier-image`** | lab | f | `images-conteneurs/ecrire-dockerfile/` |
| **`images-premiere-image`** | lab | f | `images-conteneurs/ecrire-dockerfile/` |
| `images-ordre-des-couches` | lab | f | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-1--maximiser-le-cache-avec-lordre-des-instructions` |
| `images-contexte-de-build` | lab | f+s | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-2--utiliser-dockerignore` |
| `images-optimiser-la-taille` | lab | f | `images-conteneurs/optimiser-taille-image/` |
| `images-migrer-vers-alpine` | lab | f | `images-conteneurs/optimiser-taille-image/#choisissez-la-bonne-image-de-base` |
| `images-build-multi-etapes` | lab | f | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-3--multi-stage-build-pour-des-images-légères` |
| `images-non-root` | lab | f+s | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-4--exécuter-en-non-root` |
| `images-healthcheck` | lab | f | `moteurs-conteneurs/docker/execution-depannage/#surveiller-la-santé-avec-healthcheck` |
| `buildkit-cache-monte` | lab | f | `images-conteneurs/build/buildkit/#cache-avancé` |
| `buildkit-secret-de-build` | challenge | f+s | `moteurs-conteneurs/docker/secrets/#buildkit--secrets-au-moment-du-build` |

`images-identifier-image` est **le seul lab écrit** de ce catalogue, attesté
`VALIDE` le 2026-10-28. Il réalise le contrat `conteneurs-11` du pilotage. Son
scénario remplace une image sous le même tag et lit ce que le moteur déclare,
donc il lui faut un moteur à lui : il a été écrit en `vm` avant que la règle du
catalogue ne le soit, et c'est en le validant que la contradiction est
apparue.

`images-non-root` est marqué `security: true` et ce n'est pas décoratif :
l'audit a trouvé l'ancien TP annonçant l'utilisateur non-root comme
« optionnel ». Le lab doit faire **échouer** un cas où root nuit, pas
seulement vérifier un UID.

`buildkit-secret-de-build` est un `challenge` : son premier état fuit un secret
dans l'historique de l'image, et l'apprenant doit le retrouver avant de le
corriger. Lui donner la recette retirerait tout l'intérêt.

### `images-distribution` : distribuer ses images (6 labs)

Entièrement absent de l'ancien dépôt, pour 2 505 lignes de guides disponibles.

| id | type | val | doc_url ancré |
| --- | --- | --- | --- |
| `registry-tag-push-pull` | lab | f | `registres/#docker-push--envoyer-une-image-vers-la-registry` |
| `registry-tag-contre-digest` | lab | f+s | `registres/#tags-vs-digests--la-distinction-critique` |
| `images-epingler-par-digest` | lab | f+s | `registres/#tags-vs-digests--la-distinction-critique` |
| `registry-locale-tls` | lab | f+s | `registres/distribution/#configurer-tls` |
| `registry-authentification` | lab | f+s | `registres/distribution/#configurer-lauthentification` |
| `registry-air-gap` | challenge | f | `outils/skopeo/#environnements-air-gap-déconnectés` |

`registry-locale-tls` et `registry-authentification` touchent la configuration
du démon pour lui faire accepter un certificat. C'était l'argument qui les
mettait en `vm` quand les autres étaient sur le poste ; il devient l'argument
qui montre pourquoi la VM est la bonne règle pour tous. `insecure-registries`
ne doit pas être le chemin nominal, le brief le demande explicitement.

`registry-air-gap` prépare l'**épreuve 2** du niveau : livrer une image
utilisable ailleurs, sans accès au registre d'origine.

---

## Niveau c3 : exploiter une application avec Compose

### `compose-application` : décrire une application avec Compose (9 labs)

| id | type | val | doc_url ancré |
| --- | --- | --- | --- |
| `compose-premiere-stack` | lab | f | `orchestrateurs/docker-compose/#votre-premier-composeyaml` |
| `compose-resolution-des-variables` | lab | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-isolation-reseau` | lab | f+s | `orchestrateurs/docker-compose/#concepts-clés` |
| `compose-persistance` | lab | f | `orchestrateurs/docker-compose/#concepts-clés` |
| `compose-tache-de-migration` | lab | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-secrets` | lab | f+s | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-sante-et-dependances` | lab | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-ressources` | lab | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-plusieurs-environnements` | lab | f | `orchestrateurs/docker-compose/#configuration-avancée` |

**Ce bloc tient sur un guide de 798 lignes dont les sections sont larges.**
Les ancres ci-dessus sont justes, mais `#configuration-avancée` sert six labs :
le guide traite variables, secrets, santé, profils, limites et surcharges dans
une seule section. Le `doc_url` est donc exact sans être précis.

À remonter au blog plutôt qu'à contourner ici : six sous-sections nommées
rendraient six ancres distinctes, et le catalogue Compose y gagnerait autant
que le lecteur du guide. Le programme cible le prévoit déjà, puisqu'il découpe
ce module en huit leçons.

### `compose-exploitation` : exploiter une application Compose (2 labs)

| id | type | val | prér. | doc_url ancré |
| --- | --- | --- | --- | --- |
| `donnees-postgres-sauvegarde` | challenge | f | - | `moteurs-conteneurs/docker/volumes/#sauvegarderestauration-des-volumes-docker` |
| `compose-capstone` | capstone | f+s | les labs de `compose-application` | `orchestrateurs/docker-compose/` |

**Ce module est le trou que le reclassement a mis au jour.** Il annonce quatre
leçons et ne reçoit que deux labs : la sauvegarde est couverte, le capstone
sert d'épreuve 3, mais **la lecture des journaux, la mesure des ressources
d'une stack, la mise à jour et le retour arrière n'ont aucun lab**. Trois ou
quatre labs sont à écrire ici, et ils se décrivent avant de se coder.

`donnees-postgres-sauvegarde` quitte le bloc « persister » de l'ancien
découpage : sauvegarder une base, c'est exploiter une application, pas monter
un volume.

---

## Niveau c4 : fiabiliser, sécuriser et industrialiser

### `docker-administration` : administrer et durcir un hôte (17 labs)

| id | type | val | doc_url ancré |
| --- | --- | --- | --- |
| `docker-configurer-le-demon` | lab | f | `moteurs-conteneurs/docker/daemon-config/` |
| `docker-contexte-ssh` | lab | f+s | `moteurs-conteneurs/docker/daemon-config/#structure-et-syntaxe` |
| `docker-rotation-des-journaux` | lab | f | `moteurs-conteneurs/docker/daemon-config/#logging-drivers` |
| `securite-groupe-docker` | lab | f+s | `moteurs-conteneurs/docker/securite/#comprendre-le-modèle-de-menaces-docker` |
| `securite-socket-lecture-seule` | challenge | f+s | `moteurs-conteneurs/docker/socket-proxy/#pourquoi-ro-ne-suffit-pas` |
| `securite-socket-proxy` | lab | f+s | `moteurs-conteneurs/docker/socket-proxy/` |
| `securite-rootless` | lab | f+s | `moteurs-conteneurs/docker/securite/#rootless-mode` |
| `securite-capabilities` | lab | f+s | `moteurs-conteneurs/docker/sous-le-capot/#capabilities--fragmenter-les-privilèges-root` |
| `securite-no-new-privileges` | lab | f+s | `moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime` |
| `securite-seccomp` | lab | f+s | `moteurs-conteneurs/docker/securite/#profils-seccomp` |
| `securite-apparmor` | lab | f+s | `moteurs-conteneurs/docker/securite/#apparmor-et-selinux` |
| `container-systeme-en-lecture-seule` | lab | f+s | `moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime` |
| `container-limite-de-processus` | lab | f+s | `moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime` |
| `secrets-au-runtime` | lab | f+s | `moteurs-conteneurs/docker/secrets/#injection-au-runtime--autres-méthodes` |
| `container-memoire-et-oom` | lab | f | `moteurs-conteneurs/docker/execution-depannage/#diagnostic-approfondi--le-cas-oom-kill` |
| `troubleshoot-disque-plein` | challenge | f | `moteurs-conteneurs/docker/daemon-config/#optimisations-production` |
| `donnees-volume-orphelin` | challenge | f | `moteurs-conteneurs/docker/volumes/#bonnes-pratiques-de-gestion-des-volumes` |

C'est le module le plus chargé du backlog, et c'est cohérent : il réunit les
sept leçons qui vont du démon au diagnostic, et la sécurité n'y est pas un
chapitre à part mais la façon de tenir l'hôte.

`securite-socket-lecture-seule` est le lab que le brief appelle « très
important », et il mérite son statut de challenge : il doit prouver que
`/var/run/docker.sock` monté en `:ro` laisse une requête POST modifier le
moteur. **Un système de fichiers en lecture seule n'est pas une API en lecture
seule.**

`securite-apparmor` demande une vérification que la VM ne dispense pas : ne
jamais prétendre avoir validé AppArmor dans un environnement qui ne l'applique
pas. Le catalogue Kubernetes a mesuré exactement cela, un kubelet refusant un
profil faute d'AppArmor actif dans le nœud. Le lab doit donc constater
qu'AppArmor est **actif** sur l'image Debian 13 du catalogue, et refuser de
noter s'il ne l'est pas.

`container-memoire-et-oom` doit faire constater ce que le brief souligne :
`exit 137` **ne prouve pas** un OOM. Le test lit `.State.OOMKilled`, le code de
sortie et `docker events`, et le scénario produit un `137` sans OOM pour que la
confusion se voie.

`donnees-volume-orphelin` reprend le piège que le brief nomme : un volume
`dangling` n'est pas un volume inutile. Le challenge doit rendre `docker volume
prune` **destructeur** dans son contexte, et le test vérifie que les données
sont toujours là à la fin. Il tient ici parce qu'il relève de l'entretien d'un
hôte, pas de la découverte des volumes.

`troubleshoot-disque-plein` porte `snapshot_required: true` : il remplit le
disque à dessein, et un lab qui annonce un filet de sécurité doit réellement en
avoir un. Même chose pour les trois labs de démon, qui modifient
`daemon.json` et redémarrent le service.

L'étape NFS de l'ancien TP5 ne figure nulle part : elle exige un serveur NFS,
donc un second hôte, et elle attendra qu'un guide la couvre.

### `docker-industrialisation` : industrialiser la livraison (3 labs)

| id | type | val | prér. | doc_url ancré |
| --- | --- | --- | --- | --- |
| `compose-dans-une-ci` | challenge | f | - | `orchestrateurs/docker-compose/#commandes-essentielles` |
| `image-scan-de-vulnerabilites` | lab | f+s | - | `registres/quay-io/#publier-une-image-sur-quayio` |
| `capstone-chaine-complete` | capstone | f+s | les capstones des trois niveaux précédents | - |

`image-scan-de-vulnerabilites` doit corriger l'erreur de l'ancien TP3 : le lab
fait constater qu'un scan est un **état daté**, et son test ne dépend pas du
fait qu'une image publique soit encore vulnérable demain. La fixture est
maîtrisée.

`capstone-chaine-complete` est l'**épreuve 4**, celle du §18 du brief : source,
multi-étapes, BuildKit, SBOM, registry, pull par digest, Compose, API et
PostgreSQL, volume, isolation réseau, secret, non-root, limites, santé. Puis
huit pannes injectées, sans que le sujet soit annoncé.

**Second trou du reclassement** : ce module annonce cinq leçons, dont la
promotion d'un artefact entre environnements et la préparation à
l'exploitation, et il n'a aucun lab pour elles. Deux à écrire.

---

## Hors tronc : Docker Swarm (18 labs)

`projet.perimetre.hors_tronc` de `docker.yaml` écarte explicitement Swarm :
« Kubernetes et Swarm: parcours distincts ». Ces dix-huit labs n'ont donc
**aucun module en face**, et la section `swarm-hors-tronc` de `meta.yml` le
déclare. Ce n'est pas un défaut d'alignement : c'est une décision de périmètre.

Les identifiants sont ceux du brief, qui les a nommés précisément. Leur
`doc_url` vise les sections du guide Swarm, dont les 20 ancres sont vérifiées.

| Bloc | Labs | Ancre de référence |
| --- | --- | --- |
| cluster | `swarm-init`, `swarm-ajouter-des-workers`, `swarm-trois-managers`, `swarm-quorum` | `#initialisation-dun-cluster-docker-swarm`, `#quorum-et-tolérance-aux-pannes` |
| services | `swarm-service-replique`, `swarm-service-global`, `swarm-placement`, `swarm-drainer-un-noeud` | `#services-globaux-vs-répliqués`, `#contraintes-de-placement`, `#maintenance-des-nœuds` |
| réseau | `swarm-overlay`, `swarm-vip-et-dnsrr`, `swarm-routing-mesh` | `#réseaux-overlay`, `#routing-mesh-et-load-balancing`, `#modes-de-publication-des-ports` |
| données | `swarm-rotation-des-secrets`, `swarm-configs`, `swarm-piege-du-volume-local` | `#gestion-des-secrets`, `#secrets-dans-une-stack` |
| updates | `swarm-rolling-update`, `swarm-rollback` | `#stratégies-de-mise-à-jour`, `#rollback-automatique` |
| sécurité et DR | `swarm-autolock`, `swarm-perte-de-quorum` | `#rotation-des-certificats`, `#forcer-un-nouveau-cluster-urgence` |
| capstone | `swarm-capstone` | le guide entier |

Leur difficulté n'est plus le runtime, puisque tout le catalogue est en VM :
c'est le **nombre** de machines. **Trois managers plus des workers, pour
dix-huit labs**, c'est une topologie sans rapport avec l'hôte unique des autres
labs. Trois pistes, à trancher avant d'écrire le premier :

1. `infra.bootstrap` de la 0.3.0 pose le cluster une fois pour toutes, empreinté
   et rejoué seulement s'il change ; les labs Swarm n'ont alors plus à
   l'installer. C'est exactement l'usage que son auteur décrit.
2. La topologie se déclare dans `meta.yml` pour tout le catalogue : un
   apprenant du premier module provisionnerait les machines de Swarm sans les
   employer. À mesurer, car c'est le défaut que le brief interdit.
3. Un catalogue séparé `swarm-dsoxlab-training` si la première piste ne suffit
   pas. Le brief l'autorise, et préfère cela à sacrifier l'expérience du
   débutant. **C'est la piste que le périmètre de la formation désigne**,
   puisqu'elle renvoie Swarm à un parcours distinct.

---

## Compte final, et ce qu'il vaut

| Niveau | Module | Labs | Écrits |
| --- | --- | --- | --- |
| c1 | `conteneurs-utilisation` | 14 | 0 |
| c1 | `conteneurs-isolation` | 10 | 0 |
| c2 | `images-construction` | 11 | **1** |
| c2 | `images-distribution` | 6 | 0 |
| c3 | `compose-application` | 9 | 0 |
| c3 | `compose-exploitation` | 2 | 0 |
| c4 | `docker-administration` | 17 | 0 |
| c4 | `docker-industrialisation` | 3 | 0 |
| hors tronc | `swarm-hors-tronc` | 18 | 0 |
| | **total** | **90** | **1** |

Le brief visait « autour de 70 labs, pas 5 ». Le backlog en compte 90 parce
qu'il part des 525 sections réellement publiées, et non d'un objectif. Treize
guides d'outils en sont écartés à dessein, ce qui aurait gonflé le compte sans
servir une compétence.

**Ce nombre n'est pas un engagement.** Le critère du §35 reste le seul : un
apprenant reçoit une application et un hôte vierge, et démontre qu'il sait. Si
quinze labs d'isolation et d'administration se révèlent redondants à
l'écriture, ils seront fusionnés, et ce sera un progrès.

**Et la répartition, elle, est un signal à lire.** Dix-sept labs face à trois,
ce n'est pas une erreur de rangement : c'est le backlog qui a grandi là où les
guides publiés étaient les plus denses, et pas là où la formation promet le plus.
Les cinq labs à écrire pour `compose-exploitation` et `docker-industrialisation`
passent donc devant les redondances à trancher.

## L'ordre d'écriture

Il suit les niveaux, dans l'ordre du parcours :

```text
1   conteneurs-utilisation                  14 labs
2   images-construction                     10 labs, après celui déjà écrit
3   conteneurs-isolation                    10 labs
4   images-distribution                      6 labs
5   compose-application                      9 labs
6   compose-exploitation                     2 labs + 3 à décrire
7   docker-administration                   17 labs
8   docker-industrialisation                 3 labs + 2 à décrire
9   swarm-hors-tronc                        18 labs, topologie à part
```

**Quand faut-il le second hôte ? La question n'est pas encore tranchée, et je
ne la tranche pas ici par déduction.** Le pilotage nomme six contrats qui
exigent deux environnements isolés, mais ce backlog a été écrit avant eux : la
correspondance entre ses identifiants de labs et les `conteneurs-NN` des
contrats n'est pas établie. Deux d'entre eux relèvent de modules qui arrivent
tôt (`conteneurs-18` en construction, `conteneurs-32` en persistance), donc le
second hôte peut être nécessaire dès les premières étapes.

Ce qui se fait avant d'écrire ces labs, dans cet ordre : établir la
correspondance contrat par contrat, puis ajouter l'hôte **en fin** de
`infra.hosts`. Ce qui ne se fait pas : l'ajouter d'avance, ce qui ferait
provisionner deux machines à qui joue le premier lab.
