# Écrire les labs : état du chantier et contrat d'écriture

Établi le **2026-10-29**, quand les squelettes des 70 labs du backlog ont été
créés et rangés. Ce fichier dit ce qui est déjà fait, ce qui reste à faire lab
par lab, et les règles qu'un lab doit tenir pour être attesté.

Le backlog lui-même, avec le `doc_url` ancré de chaque lab et la justification
de son découpage, vit dans `ROADMAP.md`. Ce fichier-ci ne le répète pas : il
décrit le **geste d'écriture**.

## Ce qui est déjà fait, et qu'il ne faut pas refaire

Reprise du **2026-11-01** sur `chantier/labs-restants` : les 71 labs du
catalogue sont désormais rédigés ; aucun `lab.yaml` ne porte plus de
`a-remplir`. Les sept derniers couvrent la configuration du démon, les
contextes SSH, les journaux, les privilèges du groupe Docker, rootless et les
deux modèles d'accès au socket. La solution PostgreSQL manquante a aussi été
ajoutée.

Les sept labs terminés en dernier rendent 0 avant, 100 après, puis 0 après
`clean` et `run`, sans écart dans la photographie du moteur. Les solutions sont
chiffrées ; les consignes, indices et catalogues sont bilingues. Le contrôle
`uv run --no-sync pytest tests -q` passe (2866 réussis, 146 ignorés) et
`dsoxlab validate-structure` valide le catalogue. Le registre final compte **71 attestations valides sur 71 labs** dans
`validation-labs.json` ; le compteur se vérifie avec la commande ci-dessous.

Le validateur photographie désormais le Docker de la cible SSH des labs VM,
pas celui du poste. Il relève aussi les identifiants des images orphelines
et refuse un nettoyage qui supprime un objet préexistant. Les dix-sept labs de
cette reprise ont été rejoués avec cette mesure corrigée : 3 images de base,
0 conteneur et 0 volume dans la VM avant comme après. Les attestations
antérieures des autres labs ne constituent pas une preuve de ce nettoyage VM.

Les deux registres TLS utilisent l'adresse réseau de la VM, pas la boucle
locale que Docker traite implicitement comme insecure. Les tests retirent
temporairement la CA et mesurent un vrai refus X.509 avant de la restaurer.
Le banc air-gap a aussi été éprouvé avec une couche réellement retirée et
une somme SHA-256 recalculée : 0/2 malgré un cache Docker chaud.
Compose v2 est fourni par le paquet Debian `docker-compose`. L'image Alpine
épinglée ne contient pas l'applet HTTP ; `busybox-extras` est installé dans les
images de la première stack. La recréation forcée des deux services a été mesurée.
Les autres labs Compose mesurent la priorité du shell, les refus réseau par IP,
la persistance de nouvelles écritures, les migrations SQLite idempotentes,
les secrets fichiers après rotation, la disponibilité distincte de la sonde de vie,
les limites cgroup effectives et l'isolation de deux environnements.

| Fait | État |
|---|---|
| Labs du backlog initial | **70**, plus `images-identifier-image` déjà écrit ; les 71 sont maintenant rédigés |
| Rangement dans les neuf sections de `meta.yml` | fait, `validate-structure` rend « Tous les labs sont valides » |
| `level` (`c1` à `c4`), `doc_url` ancré, `lab_type` | **pré-remplis** depuis le backlog, dans `lab.yaml` et `lab.fr.yaml` |
| Hôte des cibles | aligné sur `docker.lab`, le seul hôte que `meta.yml` déclare |
| Labs **écrits et attestés** | le nombre d'attestations valides se mesure, voir la commande ci-dessous |
| Sections **terminées** | les huit sections du tronc commun ; `swarm-hors-tronc` reste volontairement vide |

Le compte des labs attestés ne s'écrit pas de mémoire, il se mesure :

```bash
python3 -c 'import json;d=json.load(open("validation-labs.json"));print(sum(v["verdict"]=="VALIDE" for v in d.values()),"/",len(d))'
```

Les squelettes sortent de `dsoxlab new lab`, **jamais** d'une copie d'un lab
voisin ni d'un `lab.yaml` écrit à la main : une copie emporte les écarts du
voisin, un fichier écrit à la main dérive du contrat. Un lab qui s'ajouterait
plus tard se crée de la même façon.

Deux pièges déjà payés sur ce catalogue, pour qu'ils ne reviennent pas :

- `dsoxlab new lab` **ne range pas** le lab dans une section. Il prévient que
  le lab « n'a aucune place dans la progression » ; sur d'autres catalogues, il
  l'inscrit dans la **première** section, et dix-neuf labs GitLab s'y étaient
  empilés pendant que trois sections restaient vides ;
- l'entrée d'une section s'écrit **sans** le préfixe `labs/`. Avec lui, le
  validateur cherche `labs/labs/<id>` et refuse le catalogue entier.

## Contrat à respecter pour tout nouveau lab

Il ne reste aucun squelette dans le catalogue. Cette liste décrit le contrat
pour un futur ajout ; elle n'est pas un inventaire de travaux ouverts.

Dans `labs/<id>/` :

    lab.yaml  /  lab.fr.yaml   title, description, skills, distros, validation
    scenario.md  /  .fr.md     l'énoncé que l'apprenant lit
    setup.yaml                 l'état de départ, posé par Ansible
    cleanup.yaml               ce qui défait le setup
    challenge/tests/           les assertions qui notent

`skills` et `distros` sont requis et non vides : un futur lab sans eux est
refusé, ou disparaît du catalogue sans un mot.

## Les règles qui décident si un lab est bon

### Un test doit porter sur ce que l'état de départ ne porte PAS

C'est la règle la plus souvent enfreinte, et elle a coûté quatre rejeux rouges
sur le catalogue GitLab CI. `valider-labs.py` exige un score **nul** sur l'état
de départ : un test vert avant tout travail n'est pas un test, c'est une
hypothèse du setup.

Quand une exigence est déjà vraie au départ (le service tourne, un fichier
existe), elle ne devient pas un test à elle seule : elle s'ajoute au test qui
mesure le travail réel. Et un motif cherché dans un journal doit être propre au
succès, jamais une chaîne qui apparaît aussi dans l'échec.

### La note porte sur l'état du système, jamais sur les commandes tapées

Une image qui a été construite, sa taille, l'utilisateur qui exécute le
conteneur, les montages, ce que l'application répond. Relire un fichier noterait
l'intention ; interroger le moteur note le résultat.

### Un lab se joue dans les deux sens avant d'être attesté

    python3 scripts/valider-labs.py --lab <id>

Il rejoue `clean`, `run`, `check` (attendu 0), applique la solution de
référence, `check` (attendu 100), puis `clean`. Le verdict va dans
`validation-labs.json`. Un lab sans ce cycle n'est pas livré, quel que soit son
contenu.

### Rien ne se teste sur le poste de travail

Tout tourne sur la VM `docker.lab` (Debian 13, réseau `lab-containers`,
10.10.120.0/24), déclarée dans `meta.yml`. C'est une décision éditoriale autant
que technique : on n'impose pas Docker sur la machine de l'apprenant.

### Ce que l'apprenant lit quand un test refuse existe dans les deux langues

Le message d'une assertion est la seule consigne qu'il reçoit à cet instant :
c'est de l'interface, comme un `README`. Il passe donc par le helper du
`conftest.py`, qui choisit sur `DSOXLAB_LANG` :

```python
from conftest import lab_host, message

assert f.exists, message(
    en="/etc/myapp is missing. Create it with ansible.builtin.file.",
    fr="/etc/myapp est absent. Crée-le avec ansible.builtin.file.",
)
```

Les trois porteurs de texte sont concernés : `assert …, msg`,
`pytest.fail(msg)` et `pytest.skip(msg)`. Écrire le message en anglais seul
n'est pas plus neutre que l'écrire en français seul.

`tests/test_assertions_bilingues.py` tient la règle, en parsant l'AST plutôt
qu'en cherchant un motif : savoir qu'un fichier « parle de » `message` ne dit
pas si **chaque** assertion y passe, et c'est l'écart qui compte. Il ne juge
pas la qualité d'une traduction, qui reste une relecture humaine.

La règle a été posée après coup, le 2026-10-29, et c'est ce qui en dit le plus
long. Mesure du jour : les deux catalogues livrés tenaient la convention sans
qu'aucun test ne l'exige (`publier-service` 732 messages sur 735,
`gitlab-ci` 393 sur 393), et celui-ci, avec un seul lab écrit, était déjà à
zéro sur treize.

### Les références s'épinglent, même dans un exemple

Toute image porte la forme `image:tag@sha256:…`. Jamais `:latest`, jamais un
tag seul.

`tests/test_images_epinglees.py` contrôle ce que **le dépôt exécute lui-même**,
`setup.yaml` et `cleanup.yaml`, là où un tag flottant rend le lab non
reproductible. Les `fixtures/` sont hors périmètre, et ce n'est pas un oubli :
`scripts/hooks/hadolint-cible.sh` a déjà tracé cette frontière et nomme
« image de base en tag flottant » parmi les sujets d'exercice légitimes.

Un contre-exemple volontaire porte un marqueur, avec sa raison :

```yaml
    # dsoxlab:tag-nu-volontaire : <pourquoi l'épingler casserait ce lab>
    - name: La tâche qui consomme la référence nue
```

Le marqueur vaut pour **sa tâche**, jusqu'à la ligne vide qui la précède, et
jamais pour le fichier : une exemption posée en tête couvrirait les références
ajoutées plus tard sans que personne ne le décide.

Le cas existe déjà, et il justifie la nuance : `images-identifier-image`
demande le digest de `debian:13` « telle qu'elle est sur cette machine ».
Épingler son `docker pull` écrirait la réponse attendue dans le setup, et le
lab se corrigerait lui-même. Noter aussi que le marqueur ne peut pas être posé
dans un bloc `content: |` : il serait écrit dans le Dockerfile livré à
l'apprenant.

## L'ordre d'écriture

Celui du parcours, et il est déjà justifié dans `ROADMAP.md`. Le reste-à-faire
ci-dessous est celui du **2026-10-30 au soir**, deux sections étant terminées :

    1  conteneurs-utilisation       TERMINEE, 14 labs sur 14
    2  conteneurs-isolation         TERMINEE, 10 labs sur 10
    3  images-construction          2 labs restants sur 10
    4  images-distribution          6 labs
    5  compose-application          9 labs
    6  compose-exploitation         2 labs
    7  docker-administration       17 labs
    8  docker-industrialisation     3 labs

Ce décompte est à relire par la mesure plutôt qu'à croire : les labs écrits
sont ceux que `validation-labs.json` atteste, et les squelettes restants ceux
dont le `lab.yaml` porte encore `a-remplir`.

```bash
grep -rl 'a-remplir' labs --include='lab.yaml' | wc -l
```

Deux sections passent devant leur rang si l'on veut corriger un déséquilibre
réel : `compose-exploitation` et `docker-industrialisation` n'ont que cinq labs
à eux deux, pour quatre leçons annoncées chacun. Le backlog a grandi là où les
guides publiés étaient les plus denses, pas là où la formation promet le plus.

## Ce que le catalogue ne décide pas

Un lab ne devient visible pour un lecteur que lorsqu'une page du site pose son
bloc `<Lab>`. Aucune page ne cite encore ce catalogue : le câblage est un
travail du dépôt du site, et il suit la livraison, il ne la précède pas.

Le dépôt se commite **en local**. La livraison est un geste humain.

## Reprendre le travail : l'état au soir du 2026-10-30

### Sur quelle branche

**`chantier/labs-restants`**, et pas une autre. Elle part de `main` et porte les
71 labs : les 32 attestés et les 39 au gabarit.

`main` ne porte que les **32 labs attestés** : la livraison du 2026-10-30 a
écarté les squelettes pour qu'ils n'apparaissent pas au catalogue avant d'avoir
été écrits. Les y ramener serait une régression, pas une mise à jour.

`feat/section-conteneurs-utilisation` est l'ancienne branche de travail. Ses 44
commits sont déjà sur `main` sous la forme d'un seul, par un merge en squash :
en ouvrir une PR les rejouerait et ramènerait les squelettes. GitHub propose ce
bouton de lui-même, et il ne faut pas le suivre.

### Le prochain lab, et ce qui est déjà mesuré pour lui

`images-construction` n'a plus que **`buildkit-cache-monte`** et
**`buildkit-secret-de-build`**.

Pour le second, les mesures sont faites, sur `docker.lab` le 2026-10-30. Elles
ont coûté une VM et un quart d'heure, et elles portent le lab en entier :

| Façon de passer le secret | Dans l'environnement | Dans `docker history` | Dans l'archive des couches |
| --- | --- | --- | --- |
| `--build-arg` | non | **oui** | non |
| `COPY` puis `rm` | non | non | **oui**, une occurrence |
| `--mount=type=secret` | non | non | **non**, zéro occurrence |

Deux choses à en tirer pour l'écriture. Le `--build-arg` ne laisse rien dans le
conteneur et **reste dans l'historique de l'image**, que `docker history` rend
en clair : c'est la fuite qu'on ne voit pas en inspectant le conteneur. Et le
`COPY` suivi d'un `rm` est le même défaut que `images-optimiser-la-taille` : la
couche garde le fichier, et `docker save` le montre.

La mesure se refait avec le script du scratchpad de la session, ou se réécrit en
dix lignes : construire trois images, chercher la chaîne du secret dans
`docker history`, puis dans l'archive produite par `docker save`.

Pour `buildkit-cache-monte`, **rien n'est mesuré** : tout reste à faire.

### Les gestes de reprise, dans l'ordre

```bash
cd ~/Projets/containers-dsoxlab-training
git switch chantier/labs-restants && git pull
git switch main && git pull && git switch chantier/labs-restants
git rebase main                     # main a pu avancer, la CI y est verte
dsoxlab doctor                      # la VM docker.lab doit repondre
```

Puis le contrat d'écriture de ce fichier s'applique sans changement : squelette
de `dsoxlab new lab`, mesure avant d'écrire, tests qui notent zéro sur l'état de
départ, et `python3 scripts/valider-labs.py --lab <id>` qui doit rendre VALIDE
dans les deux sens avant tout commit.

### Ce qui attend une action humaine

La **PR #20** (montée de `jdx/mise-action`) attend une réapprobation : une mise
à jour de sa branche a invalidé l'approbation précédente, la règle
`require_last_push_approval` étant active.

La branche `feat/section-conteneurs-utilisation` peut être supprimée : son
contenu est à deux endroits, les 32 labs sur `main` et les 39 squelettes sur
`chantier/labs-restants`, ce dernier point ayant été vérifié lab par lab.
