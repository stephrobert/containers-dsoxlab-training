# Couverture : guides, compétences, labs

Matrice établie le 2026-10-01 par inventaire du blog, pas de mémoire. Elle
répond à la seule question qui pilote ce catalogue :

> Quelles compétences de la formation Conteneurs un apprenant peut-il
> **démontrer** lui-même, et non reconnaître dans un quiz ?

## Ce que l'inventaire a mesuré

```console
$ python3 scripts/inventaire-guides.py
42 guides dans le périmètre, 525 sections au total
```

Le périmètre exclut Kubernetes (60 guides, son propre catalogue), Incus (33),
Podman (13) et l'outillage Kubernetes (36 + 20 Helm). Il reste 42 guides, dont
**16 portent déjà un quiz** et **3 un bloc de travaux pratiques**.

### Les guides sont concentrés, et c'est la contrainte de conception

| Guide | Lignes | Sections | Labs visés |
| --- | --- | --- | --- |
| `orchestrateurs/docker-swarm` | 1095 | 20 | 18 à 20 |
| `moteurs-conteneurs/docker/securite` | 976 | 17 | 10 |
| `moteurs-conteneurs/docker/volumes` | 903 | 16 | 4 |
| `moteurs-conteneurs/docker/daemon-config` | 868 | 15 | 2 |
| `images-conteneurs/ecrire-dockerfile` | 863 | 10 | 2 |
| `orchestrateurs/docker-compose` | 798 | 15 | 10 à 12 |

Un `doc_url` qui pointe la page entière n'apprend plus rien quand vingt labs
pointent la même. **L'ancre de section est donc la règle de ce catalogue**, et
elle est vérifiée : le slugifieur tombe juste 114 fois sur 114 contre les pages
publiées. Voir `AUDIT.md` pour la règle exacte, qui ne se devine pas.

## La matrice

Colonnes : le guide, la compétence qu'il sert, s'il porte un quiz côté blog, le
lab de l'ancien dépôt s'il existait, et le lab cible.

| Guide | Compétence | Quiz | Ancien | Lab cible | État |
| --- | --- | --- | --- | --- | --- |
| `docker/index` | c1 panorama | non | - | - (page d'entrée) | sans objet |
| `docker/installation` | c1 installer | oui | - | `docker-verifier-son-moteur` | à écrire |
| `docker/concepts` | c1 comprendre | oui | - | `docker-image-vs-conteneur`, `docker-anatomie-image` | à écrire |
| `docker/cli` | c1 manipuler | oui + TP | - | `docker-premier-conteneur`, `docker-cycle-de-vie`, `docker-inspecter` | à écrire |
| `images-conteneurs/index` | c1 anatomie | oui | - | `docker-anatomie-image`, `docker-save-load` | à écrire |
| `images-conteneurs/ecrire-dockerfile` | c2 construire | oui | TP1 | **`images-premiere-image`** | **validé** |
| `images-conteneurs/dockerfile-bonnes-pratiques` | c2 cache, non-root | oui | TP4 | `images-ordre-des-couches`, `images-non-root`, `images-build-multi-etapes` | 1 squelette |
| `images-conteneurs/optimiser-taille-image` | c2 alléger | oui | TP2, TP3 | `images-optimiser-la-taille`, `images-migrer-vers-alpine` | 2 squelettes |
| `images-conteneurs/build/buildkit` | c2 BuildKit | oui | - | `buildkit-cache-monte`, `buildkit-secret`, `buildx-multiarch` | à écrire |
| `images-conteneurs/build/bake` | c2 build déclaratif | non | - | - (hors cœur, vague tardive) | écarté v1 |
| `images-conteneurs/build/buildah`, `kaniko`, `buildpacks` | c2 alternatives | non | - | - | écarté v1 |
| `images-conteneurs/controle-connaissances` | c2 quiz | c'est le quiz | - | - | sans objet |
| `registres/index` | c3 distribuer | oui | - | `registry-tag-push-pull`, `image-tag-vs-digest` | à écrire |
| `registres/distribution` | c3 registry privée | non | - | `registry-locale-tls`, `registry-auth` | à écrire |
| `registres/docker-hub` | c3 publier | non | - | `registry-publier-sur-docker-hub` | à écrire |
| `registres/quay-io`, `orca` | c3 variantes | 1 sur 2 | - | - | écarté v1 |
| `outils/skopeo` | c3 air-gap | non | - | `registry-air-gap` | à écrire |
| `outils/crane`, `oras` | c3 outillage | non | - | - (servent un lab, pas un module) | écarté v1 |
| `docker/execution-depannage` | c4 exécuter, c7 dépanner | oui | - | `container-entrypoint-cmd`, `container-signaux-pid1`, `container-memoire-oom`, `troubleshoot-exit-127`, `troubleshoot-boucle-de-redemarrage` | à écrire |
| `docker/volumes` | c5 persister | oui + TP | TP5 | **`donnees-volumes-et-montages`**, `donnees-volume-orphelin`, `donnees-permissions`, `donnees-postgres-sauvegarde` | 1 squelette |
| `docker/network` | c5 connecter | oui + TP | - | `reseau-bridge-par-defaut`, `reseau-bridge-dedie`, `reseau-publication-de-ports`, `reseau-interne`, `reseau-diagnostic-dns` | à écrire |
| `orchestrateurs/docker-compose` | c6 composer | non | coquille vide | 10 labs `compose-*` | à écrire |
| `docker/daemon-config` | c7 exploiter | oui | - | `docker-daemon-config`, `docker-rotation-des-journaux` | à écrire |
| `docker/securite` | c8 sécuriser | oui | - | `securite-groupe-docker`, `securite-capabilities`, `securite-no-new-privileges`, `securite-rootless`, `securite-seccomp` | à écrire |
| `docker/secrets` | c8 secrets | oui | - | `secrets-au-build`, `secrets-au-runtime` | à écrire |
| `docker/socket-proxy` | c8 socket | oui | - | `securite-socket-lecture-seule`, `securite-socket-proxy` | à écrire |
| `docker/sous-le-capot` | c9 internes | oui | - | `internes-namespaces`, `internes-cgroups-v2`, `internes-chaine-dexecution` | à écrire |
| `outils/dive` | c2 mesurer | non | TP2 (dive) | sert `images-ordre-des-couches` | outil |
| `outils/hadolint` | c2 lint | non | - | sert `images-ordre-des-couches` | outil |
| `outils/container-struct-test` | c2 tester | non | - | - | écarté v1 |
| `outils/dozzle`, `lazydocker`, `crictl` | c7 confort | non | - | - | écarté v1 |
| `containerd/index`, `nerdctl-base` | c9 moteur | non | - | sert `internes-chaine-dexecution` | outil |
| `orchestrateurs/docker-swarm` | sw1 à sw7 | oui | coquille vide | 18 labs `swarm-*` | vague 6 |

## Ce que la matrice fait apparaître

**Trois trous majeurs dans l'ancien dépôt**, et ce sont les plus utiles en
production :

| Compétence | Guides disponibles | Labs d'avant |
| --- | --- | --- |
| c3, distribuer les images | 7 guides, 2 505 lignes | **aucun** |
| c7, exploiter et dépanner | 3 guides, 2 176 lignes | **aucun** |
| c8, sécuriser | 3 guides, 1 896 lignes | **aucun** |

L'ancien dépôt couvrait la construction d'images, et rien de ce qui vient
après. Un apprenant en sortait capable de produire une image, sans savoir la
distribuer, la durcir ni diagnostiquer son conteneur.

**Un guide sans quiz n'est pas un guide sans matière.** `docker-compose` n'a pas
de quiz et porte 798 lignes et 15 sections : c'est le bloc c6 entier.
Inversement, `images-conteneurs/controle-connaissances` est un quiz pur, sans
lab à lui jumeler.

**Les guides d'outils ne méritent pas de module.** Skopeo, Crane, ORAS, Dive,
Hadolint sont des outils : ils servent une compétence et apparaissent dans le
lab qui en a besoin, conformément au §9 du brief. Treize guides sont écartés de
la première version pour cette raison, et c'est une décision, pas un oubli.

## Le portail de la formation

Le blog porte une page de parcours avec suivi de progression :

```console
$ curl -s -o /dev/null -w '%{http_code}' -L \
    https://blog.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/parcours/
200
```

Son frontmatter annonce « 5 modules, 11 leçons » et un composant
`FormationProgramme` à cocher. C'est le candidat naturel pour le
`learning.portal_url` que dsoxlab 0.3.0 introduit.

**Décision laissée à Stéphane** : le contrat décrit `portal_url` comme une URL
de **remise** d'une preuve d'apprentissage, et cette page est un programme à
cocher. Les deux se ressemblent sans se confondre, et inscrire la seconde à la
place de la première ferait dire à dsoxlab quelque chose que le site ne fait
pas. Le champ reste donc vide jusqu'à arbitrage.

## Comment cette matrice se tient à jour

`scripts/inventaire-guides.py` régénère l'inventaire depuis le blog local. La
colonne « État » se met à jour à la main, et `scripts/valider-labs.py` est ce
qui autorise à écrire « validé » : un lab y est **VALIDE** quand son `check`
rend 0 avant le travail et 100 après.
