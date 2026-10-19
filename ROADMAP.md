# Backlog des labs

Établi le 2026-10-01 depuis la matrice de `COVERAGE.md`. Chaque ligne porte le
`doc_url` **ancré** sur la section que le lab éprouve.

**Les 64 ancres de ce backlog sont vérifiées contre les pages publiées :**

```console
$ python3 scripts/verifier-ancres.py
69 doc_url à contrôler
64 ancre(s) juste(s), 0 fausse(s), 0 page(s) injoignable(s), 5 doc_url sans ancre
```

Et il a fallu ce contrôle : la première rédaction de ce fichier portait
**44 ancres fausses sur 64**. Celles issues de l'inventaire du blog étaient
justes, celles écrites de mémoire étaient inventées, et rien ne les
distinguait à la lecture — un fragment faux donne un lien qui répond 200 et
dépose le lecteur en haut d'un guide de mille lignes.

`validate-structure --check-urls` ne voit pas ce défaut : il contrôle la page,
pas le fragment. `scripts/verifier-ancres.py` est né de là.

Le préfixe d'URL commun, omis dans les tableaux pour qu'ils restent lisibles :

```text
https://www.stephane-robert.info/docs/conteneurs/
```

## Comment lire ce backlog

| Colonne | Ce qu'elle dit |
| --- | --- |
| **id** | identifiant dsoxlab, en français, `<compétence>-<sujet>` |
| **type** | `lab` guidé, `challenge` sans recette, `capstone` sans sujet annoncé |
| **rt** | runtime : `sh` pour le poste de l'apprenant, `vm` pour une machine dédiée |
| **val** | `f` fonctionnel, `s` sécurité, quand le second a un sens réel |
| **prér.** | labs supposés joués, pour les capstones et les challenges |

**Le runtime n'est pas un détail.** Un lab `sh` se joue en quelques secondes
sur le moteur de l'apprenant ; un lab `vm` exige un provisionnement de
plusieurs minutes. Le brief l'exige au §20 : ne pas faire provisionner cinq
machines pour jouer le premier lab. La règle de ce catalogue est donc :

> `sh` par défaut. `vm` seulement quand le lab touche au **démon**, au
> **noyau** ou à **plusieurs hôtes** : daemon.json, rootless, seccomp,
> AppArmor, pare-feu, NFS, contexts distants, Swarm.

Ce qui donne, sur les 67 labs du backlog, **49 en `sh`** et **18 en `vm`**, et
les 18 sont tous dans les vagues 4 et 6.

---

## c1 — Comprendre et manipuler (5 labs, vague 2)

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| `docker-verifier-son-moteur` | lab | sh | f | `moteurs-conteneurs/docker/installation/#vérification-de-linstallation` |
| `docker-premier-conteneur` | lab | sh | f | `moteurs-conteneurs/docker/cli/#lancer-et-gérer-les-conteneurs-docker` |
| `docker-cycle-de-vie` | lab | sh | f | `moteurs-conteneurs/docker/concepts/#cycle-de-vie-dun-conteneur` |
| `docker-inspecter-un-conteneur` | lab | sh | f | `moteurs-conteneurs/docker/execution-depannage/#les-commandes-indispensables` |
| `docker-anatomie-dune-image` | lab | sh | f | `images-conteneurs/#comment-est-construite-une-image-de-conteneur-` |

`docker-premier-conteneur` est le lab d'entrée du catalogue : il doit se jouer
en moins d'une minute, sans rien construire, sinon il décourage avant
d'enseigner.

## c2 — Construire des images (10 labs, vague 2)

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| **`images-premiere-image`** | lab | sh | f | `images-conteneurs/ecrire-dockerfile/` |
| `images-ordre-des-couches` | lab | sh | f | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-1--maximiser-le-cache-avec-lordre-des-instructions` |
| `images-contexte-de-build` | lab | sh | f+s | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-2--utiliser-dockerignore` |
| `images-optimiser-la-taille` | lab | sh | f | `images-conteneurs/optimiser-taille-image/` |
| `images-migrer-vers-alpine` | lab | sh | f | `images-conteneurs/optimiser-taille-image/#choisissez-la-bonne-image-de-base` |
| `images-build-multi-etapes` | lab | sh | f | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-3--multi-stage-build-pour-des-images-légères` |
| `images-non-root` | lab | sh | f+s | `images-conteneurs/dockerfile-bonnes-pratiques/#principe-4--exécuter-en-non-root` |
| `images-healthcheck` | lab | sh | f | `moteurs-conteneurs/docker/execution-depannage/#surveiller-la-santé-avec-healthcheck` |
| `buildkit-cache-monte` | lab | sh | f | `images-conteneurs/build/buildkit/#cache-avancé` |
| `buildkit-secret-de-build` | challenge | sh | f+s | `moteurs-conteneurs/docker/secrets/#buildkit--secrets-au-moment-du-build` |

`images-non-root` est marqué `security: true` et ce n'est pas décoratif :
l'audit a trouvé l'ancien TP annonçant l'utilisateur non-root comme
« optionnel ». Le lab doit faire **échouer** un cas où root nuit, pas
seulement vérifier un UID.

`buildkit-secret-de-build` est un `challenge` : son premier état fuit un secret
dans l'historique de l'image, et l'apprenant doit le retrouver avant de le
corriger. Lui donner la recette retirerait tout l'intérêt.

## c3 — Distribuer les images (6 labs, vague 4)

Entièrement absent de l'ancien dépôt, pour 2 505 lignes de guides disponibles.

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| `registry-tag-push-pull` | lab | sh | f | `registres/#docker-push--envoyer-une-image-vers-la-registry` |
| `registry-tag-contre-digest` | lab | sh | f+s | `registres/#tags-vs-digests--la-distinction-critique` |
| `registry-locale-tls` | lab | vm | f+s | `registres/distribution/#configurer-tls` |
| `registry-authentification` | lab | vm | f+s | `registres/distribution/#configurer-lauthentification` |
| `registry-air-gap` | challenge | sh | f | `outils/skopeo/#environnements-air-gap-déconnectés` |
| `images-epingler-par-digest` | lab | sh | f+s | `registres/#tags-vs-digests--la-distinction-critique` |

`registry-locale-tls` et `registry-authentification` sont en `vm` : une registry
avec un certificat exige de toucher la configuration du démon de l'apprenant,
ce qu'un catalogue ne fait pas sur une machine qui n'est pas la sienne. Le brief
le demande explicitement, `insecure-registries` ne doit pas être le chemin
nominal.

## c4 — Exécuter et limiter (7 labs, vague 2 et 4)

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| `container-entrypoint-et-cmd` | lab | sh | f | `moteurs-conteneurs/docker/execution-depannage/#le-cycle-de-vie-dun-conteneur` |
| `container-signaux-et-pid-1` | lab | sh | f | `moteurs-conteneurs/docker/execution-depannage/#stop-vs-kill--quelle-différence-` |
| `container-memoire-et-oom` | lab | sh | f | `moteurs-conteneurs/docker/execution-depannage/#diagnostic-approfondi--le-cas-oom-kill` |
| `container-limite-cpu` | lab | sh | f | `moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise` |
| `container-limite-de-processus` | lab | sh | f+s | `moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime` |
| `container-systeme-en-lecture-seule` | lab | sh | f+s | `moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime` |
| `container-ulimits-et-shm` | lab | sh | f | `moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise` |

`container-memoire-et-oom` doit faire constater ce que le brief souligne :
`exit 137` **ne prouve pas** un OOM. Le test lit `.State.OOMKilled`, le code de
sortie et `docker events`, et le scénario produit un `137` sans OOM pour que la
confusion se voie.

## c5 — Persister et connecter (9 labs, vague 2)

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| `donnees-volumes-et-montages` | lab | sh | f | `moteurs-conteneurs/docker/volumes/#vue-densemble-des-types-de-volumes` |
| `donnees-volume-orphelin` | challenge | sh | f | `moteurs-conteneurs/docker/volumes/#bonnes-pratiques-de-gestion-des-volumes` |
| `donnees-permissions-uid-gid` | lab | sh | f | `moteurs-conteneurs/docker/volumes/#les-volumes-standards` |
| `donnees-postgres-sauvegarde` | challenge | sh | f | `moteurs-conteneurs/docker/volumes/#sauvegarderestauration-des-volumes-docker` |
| `reseau-bridge-par-defaut` | lab | sh | f | `moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation` |
| `reseau-bridge-dedie` | lab | sh | f | `moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation` |
| `reseau-publication-de-ports` | lab | sh | f+s | `moteurs-conteneurs/docker/network/#bonnes-pratiques-réseau` |
| `reseau-interne` | lab | sh | f+s | `moteurs-conteneurs/docker/network/#le-réseau-none--isolation-totale` |
| `reseau-diagnostic-dns` | challenge | sh | f | `moteurs-conteneurs/docker/network/#dépannage-réseau-docker` |

`donnees-volume-orphelin` reprend le piège que le brief nomme : un volume
`dangling` n'est pas un volume inutile. Le challenge doit rendre `docker volume
prune` **destructeur** dans son contexte, et le test vérifie que les données
sont toujours là à la fin.

L'étape NFS de l'ancien TP5 ne figure pas : elle exige un serveur NFS, donc un
lab `vm`, et elle attendra qu'un guide la couvre.

## c6 — Docker Compose (11 labs, vague 3)

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| `compose-premiere-stack` | lab | sh | f | `orchestrateurs/docker-compose/#votre-premier-composeyaml` |
| `compose-resolution-des-variables` | lab | sh | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-isolation-reseau` | lab | sh | f+s | `orchestrateurs/docker-compose/#concepts-clés` |
| `compose-persistance` | lab | sh | f | `orchestrateurs/docker-compose/#concepts-clés` |
| `compose-secrets` | lab | sh | f+s | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-sante-et-dependances` | lab | sh | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-tache-de-migration` | lab | sh | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-ressources` | lab | sh | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-plusieurs-environnements` | lab | sh | f | `orchestrateurs/docker-compose/#configuration-avancée` |
| `compose-dans-une-ci` | challenge | sh | f | `orchestrateurs/docker-compose/#commandes-essentielles` |
| `compose-capstone` | capstone | sh | f+s | `orchestrateurs/docker-compose/` |

**Ce bloc tient sur un guide de 798 lignes dont les sections sont larges.**
Les ancres ci-dessus sont justes, mais `#configuration-avancée` sert six labs :
le guide traite variables, secrets, santé, profils, limites et surcharges dans
une seule section. Le `doc_url` est donc exact sans être précis.

À remonter au blog plutôt qu'à contourner ici : six sous-sections nommées
rendraient six ancres distinctes, et le catalogue Compose y gagnerait autant
que le lecteur du guide.

## c7 — Exploiter et dépanner (8 labs, vague 4)

| id | type | rt | val | prér. | doc_url ancré |
| --- | --- | --- | --- | --- | --- |
| `troubleshoot-exit-127` | lab | sh | f | - | `moteurs-conteneurs/docker/execution-depannage/#décoder-les-exit-codes` |
| `troubleshoot-conflit-de-port` | lab | sh | f | - | `moteurs-conteneurs/docker/execution-depannage/#checklist-de-debug-réseau` |
| `troubleshoot-permission-refusee` | lab | sh | f | `donnees-permissions-uid-gid` | `moteurs-conteneurs/docker/volumes/#les-volumes-standards` |
| `troubleshoot-boucle-de-redemarrage` | lab | sh | f | - | `moteurs-conteneurs/docker/execution-depannage/#restart-policies--redémarrer-automatiquement` |
| `troubleshoot-disque-plein` | challenge | vm | f | - | `moteurs-conteneurs/docker/daemon-config/#optimisations-production` |
| `docker-rotation-des-journaux` | lab | vm | f | - | `moteurs-conteneurs/docker/daemon-config/#logging-drivers` |
| `docker-configurer-le-demon` | lab | vm | f | - | `moteurs-conteneurs/docker/daemon-config/` |
| `docker-contexte-ssh` | lab | vm | f+s | - | `moteurs-conteneurs/docker/daemon-config/#structure-et-syntaxe` |

`troubleshoot-disque-plein` porte `snapshot_required: true` : il remplit le
disque à dessein, et un lab qui annonce un filet de sécurité doit réellement en
avoir un. Même chose pour les trois labs de démon, qui modifient
`daemon.json` et redémarrent le service.

## c8 — Sécuriser (10 labs, vague 4)

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| `securite-groupe-docker` | lab | vm | f+s | `moteurs-conteneurs/docker/securite/#comprendre-le-modèle-de-menaces-docker` |
| `securite-capabilities` | lab | sh | f+s | `moteurs-conteneurs/docker/sous-le-capot/#capabilities--fragmenter-les-privilèges-root` |
| `securite-no-new-privileges` | lab | sh | f+s | `moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime` |
| `securite-seccomp` | lab | vm | f+s | `moteurs-conteneurs/docker/securite/#profils-seccomp` |
| `securite-apparmor` | lab | vm | f+s | `moteurs-conteneurs/docker/securite/#apparmor-et-selinux` |
| `securite-rootless` | lab | vm | f+s | `moteurs-conteneurs/docker/securite/#rootless-mode` |
| `securite-socket-lecture-seule` | challenge | vm | f+s | `moteurs-conteneurs/docker/socket-proxy/#pourquoi-ro-ne-suffit-pas` |
| `securite-socket-proxy` | lab | vm | f+s | `moteurs-conteneurs/docker/socket-proxy/` |
| `secrets-au-runtime` | lab | sh | f+s | `moteurs-conteneurs/docker/secrets/#injection-au-runtime--autres-méthodes` |
| `image-scan-de-vulnerabilites` | lab | sh | f+s | `registres/quay-io/#publier-une-image-sur-quayio` |

`securite-socket-lecture-seule` est le lab que le brief appelle « très
important », et il mérite son statut de challenge : il doit prouver que
`/var/run/docker.sock` monté en `:ro` laisse une requête POST modifier le
moteur. **Un système de fichiers en lecture seule n'est pas une API en lecture
seule.**

`securite-apparmor` est en `vm`, et le brief l'exige : ne jamais prétendre
avoir validé AppArmor dans un environnement qui ne l'applique pas. Le catalogue
Kubernetes a mesuré exactement cela, un kubelet refusant un profil faute
d'AppArmor actif dans le nœud.

`image-scan-de-vulnerabilites` doit corriger l'erreur de l'ancien TP3 : le lab
fait constater qu'un scan est un **état daté**, et son test ne dépend pas du
fait qu'une image publique soit encore vulnérable demain. La fixture est
maîtrisée.

## c9 — Comprendre sous le capot (4 labs, vague 4)

| id | type | rt | val | doc_url ancré |
| --- | --- | --- | --- | --- |
| `internes-namespaces` | lab | vm | f | `moteurs-conteneurs/docker/sous-le-capot/#namespaces--isoler-ce-que-le-conteneur-voit` |
| `internes-cgroups-v2` | lab | vm | f | `moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise` |
| `internes-stockage-des-images` | lab | sh | f | `moteurs-conteneurs/docker/sous-le-capot/` |
| `internes-chaine-dexecution` | lab | vm | f | `moteurs-conteneurs/docker/sous-le-capot/#comment-ces-mécanismes-fonctionnent-ensemble` |

`internes-stockage-des-images` reste en `sh`, et il a une raison d'exister que
l'audit a trouvée : sur cette machine, la même image mesure **83 Mio par l'API
et 329 Mio par `docker images`**, parce que le moteur emploie le containerd
image store. Le lab fait constater l'écart et dire lequel des deux chiffres
répond à quelle question.

## c10 — Capstone Docker (1 capstone, vague 5)

| id | type | rt | val | prér. |
| --- | --- | --- | --- | --- |
| `capstone-chaine-complete` | capstone | vm | f+s | les capstones de c2, c5, c6 et c8 |

Le scénario du §18 du brief : source, multi-étapes, BuildKit, SBOM, registry,
pull par digest, Compose, API et PostgreSQL, volume, isolation réseau, secret,
non-root, limites, santé. Puis huit pannes injectées, sans que le sujet soit
annoncé.

## sw1 à sw7 — Docker Swarm (18 labs, vague 6)

Les identifiants sont ceux du brief, qui les a nommés précisément. Leur
`doc_url` vise les sections du guide Swarm, dont les 20 ancres sont vérifiées.

| Bloc | Labs | Ancre de référence |
| --- | --- | --- |
| sw1 cluster | `swarm-init`, `swarm-ajouter-des-workers`, `swarm-trois-managers`, `swarm-quorum` | `#initialisation-dun-cluster-docker-swarm`, `#quorum-et-tolérance-aux-pannes` |
| sw2 services | `swarm-service-replique`, `swarm-service-global`, `swarm-placement`, `swarm-drainer-un-noeud` | `#services-globaux-vs-répliqués`, `#contraintes-de-placement`, `#maintenance-des-nœuds` |
| sw3 réseau | `swarm-overlay`, `swarm-vip-et-dnsrr`, `swarm-routing-mesh` | `#réseaux-overlay`, `#routing-mesh-et-load-balancing`, `#modes-de-publication-des-ports` |
| sw4 données | `swarm-rotation-des-secrets`, `swarm-configs`, `swarm-piege-du-volume-local` | `#gestion-des-secrets`, `#secrets-dans-une-stack` |
| sw5 updates | `swarm-rolling-update`, `swarm-rollback` | `#stratégies-de-mise-à-jour`, `#rollback-automatique` |
| sw6 sécurité et DR | `swarm-autolock`, `swarm-perte-de-quorum` | `#rotation-des-certificats`, `#forcer-un-nouveau-cluster-urgence` |
| sw7 capstone | `swarm-capstone` | le guide entier |

Tous en `runtime: vm`, et c'est la question ouverte du §20 : **trois managers
plus des workers, pour dix-huit labs, imposeraient un provisionnement lourd à
qui veut jouer le premier lab Docker.** Trois pistes, à trancher avant la
vague 6 :

1. `infra.bootstrap` de la 0.3.0 pose le cluster une fois pour toutes, empreinté
   et rejoué seulement s'il change ; les labs Swarm n'ont alors plus à
   l'installer. C'est exactement l'usage que son auteur décrit.
2. La topologie se déclare dans `meta.yml` pour tout le catalogue : un
   apprenant du bloc c1 provisionnerait les machines de Swarm sans les
   employer. À mesurer, car c'est le défaut que le brief interdit.
3. Un catalogue séparé `swarm-dsoxlab-training` si la première piste ne suffit
   pas. Le brief l'autorise, et préfère cela à sacrifier l'expérience du
   débutant.

---

## Compte final, et ce qu'il vaut

| Bloc | Labs | Vague |
| --- | --- | --- |
| c1 comprendre | 5 | 2 |
| c2 construire | 10 | 2 |
| c3 distribuer | 6 | 4 |
| c4 exécuter | 7 | 2 et 4 |
| c5 persister et connecter | 9 | 2 |
| c6 Compose | 11 | 3 |
| c7 exploiter | 8 | 4 |
| c8 sécuriser | 10 | 4 |
| c9 internes | 4 | 4 |
| c10 capstone | 1 | 5 |
| sw1 à sw7 Swarm | 18 | 6 |
| **total** | **89** | |

Le brief visait « autour de 70 labs, pas 5 ». Le backlog en compte 89 parce
qu'il part des 525 sections réellement publiées, et non d'un objectif. Treize
guides d'outils en sont écartés à dessein, ce qui aurait gonflé le compte sans
servir une compétence.

**Ce nombre n'est pas un engagement.** Le critère du §35 reste le seul : un
apprenant reçoit une application et un hôte vierge, et démontre qu'il sait. Si
quinze labs de c4 et c9 se révèlent redondants à l'écriture, ils seront
fusionnés, et ce sera un progrès.

## L'ordre d'écriture

```text
vague 2   c1, c2, c4 (partie sh), c5         31 labs, tous en runtime shell
vague 3   c6                                 11 labs
vague 4   c3, c7, c8, c9, c4 (partie vm)     28 labs, dont les 18 en vm
vague 5   c10                                 1 capstone
vague 6   sw1 à sw7                          18 labs, après arbitrage topologie
```

La vague 2 est entièrement jouable sans provisionner une seule machine. C'est
voulu : à son terme, la formation est déjà utilisable par quelqu'un qui n'a
qu'un Docker sur son poste.
