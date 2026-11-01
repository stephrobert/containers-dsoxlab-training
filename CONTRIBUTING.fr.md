# Contribuer

**Langue :** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

Merci de vouloir améliorer ce catalogue. Ce document dit ce qu'un lab doit
porter, et surtout **ce qui fait refuser une contribution**, pour que vous ne
l'appreniez pas après l'avoir écrite.

## La règle qui gouverne tout le reste

> Un test qui passe ne prouve rien tant qu'on n'a pas vu **échouer** ce qui
> doit échouer.

Un lab se mesure dans les deux sens : score **nul** avant le travail, **plein**
après. Un lab qui rend des points sans qu'on ait rien fait ne mesure pas une
compétence, il mesure son propre état de départ.

```bash
dsoxlab run   <id>    # le point de départ est posé
dsoxlab check <id>    # DOIT rendre 0
# puis la solution de référence, dans challenge/work
dsoxlab check <id>    # DOIT rendre 100
```

`scripts/valider-labs.py` fait ce cycle, et davantage : il photographie le
moteur Docker avant et après, et une image, un volume, un conteneur ou un
réseau laissé derrière rend le lab **ROUGE**. Ce n'est pas du zèle : c'est le
lab suivant qui en paierait le prix, en trouvant un état qu'il n'a pas posé.

```bash
python3 scripts/valider-labs.py --lab <id>
```

Pour les preuves couvrant les contrats complets du parcours, mesurez aussi
le second passage :

```bash
LAB_HOME=$PWD python3 scripts/valider-labs.py --lab <id> --double-passage
python3 scripts/valider-labs.py --check --lab <id> --double-passage
```

Le protocole mesuré est `0 → plein → 0 → plein → propre`. La relecture stricte
refuse un ancien relevé sans second succès effectivement mesuré : ni skip ni
contrôle absent ne deviennent un succès. Cette option est incompatible avec
`--sans-rejeu`.

Docker doit exister avant la photographie pré-setup. `infra/bootstrap.yaml`
prépare ce socle VM. `runtime.targets` sélectionne des cibles alternatives ;
les hôtes simultanés appartiennent aux `roles` de la cible sélectionnée et
deviennent des groupes d'inventaire `lab_<role>`. Le validateur photographie
tous ces hôtes ; le rejeu de référence reçoit les mêmes rôles. Chaque moteur
doit rester intact. Ajoutez les nouveaux hôtes en fin de `infra.hosts` pour
préserver les adresses existantes et sérialisez les cycles VM : jamais deux
attestations concurrentes.

## Ce que votre lab doit porter

| Fichier | Rôle |
| --- | --- |
| `lab.yaml` | le contrat : `level` = la compétence, `doc_url` = la leçon **ancrée** |
| `lab.fr.yaml` | `title` et `description` en français, et **rien d'autre** |
| `scenario.md`, `.fr.md` | la **situation** et l'objectif, jamais un mode d'emploi |
| `README.md`, `.fr.md` | le tutoriel : le mécanisme, sur des exemples jetables |
| `challenge/README.md`, `.fr.md` | l'**énoncé**, en exigences numérotées |
| `challenge/hints.yaml` | quatre indices en base64, bilingues, à coût croissant |
| `challenge/tests/test_functional.py` | la preuve. Le nom est imposé par le contrat |
| `fixtures/` | le point de départ, copié dans `challenge/work` par `dsoxlab run` |
| `solution/` | la solution de référence, posée par-dessus pour la validation |

Une fixture **déclarée** dans `lab.yaml` doit exister dans `fixtures/`, et une
fixture présente mais non déclarée n'est **pas** copiée. Le premier cas est
refusé par `dsoxlab validate-structure`, le second donne un répertoire de
travail incomplet sans qu'aucun message le dise.

## Ce qui fait refuser une contribution

### Un test qui lit les commandes au lieu de l'état

```python
# NON
assert "docker build" in historique

# OUI
assert inspecter_image(tag)["Config"]["ExposedPorts"]
code, corps = conteneur.repondre("/health")
assert conteneur.utilisateur() != "0"
```

L'apprenant arrive au résultat par le chemin qu'il veut. On interroge le moteur,
jamais un historique.

### Un test vrai avant le travail

C'est le défaut le plus fréquent du domaine. « Docker répond », « l'application
démarre », « le fichier existe » : tous vrais avant que l'apprenant ait touché
à quoi que ce soit, parce que c'est le setup qui les a rendus vrais.

> Avant d'écrire un test, demandez-vous : « serait-il vert si le candidat ne
> faisait rien ? » Si oui, ce n'est pas un test, c'est une hypothèse du setup.

La forme juste est de **fusionner** cette moitié dans le test final, où elle ne
peut être atteinte qu'après le travail. Exemple, dans
`images-premiere-image` : « l'application répond » est vrai dès le premier
contrôle ; réuni à « sans aucun réseau », il distingue une image autonome d'une
image qui télécharge au démarrage.

### Un test qui mesure trop tôt

Un service dans un conteneur n'écoute pas à la seconde où le conteneur existe.
`Conteneur.repondre()` réessaie dans un budget borné, et il faut s'en servir :
**un faux négatif vaut pire qu'un test absent**, parce qu'il recale un
apprenant dont le travail est juste.

### Un objet Docker laissé derrière

Tout ce qu'un test crée porte le préfixe `dsoxlab-<lab>-` et est retiré en
`finally`. `conftest.py` fournit `image_temporaire`, `conteneur_temporaire` et
`volume_temporaire` pour que ce soit le chemin le plus court.

Deux raisons : le préfixe écarte toute collision avec une image de l'apprenant
qui s'appellerait « inventaire », et le retrait systématique permet au
validateur de constater que rien n'a bougé.

### Un `doc_url` dont l'ancre n'existe pas

Les guides du blog sont concentrés : 1095 lignes pour Swarm, 798 pour Compose.
Un lab vise donc la **section** qu'il éprouve, et il faut le vérifier :

```bash
python3 scripts/verifier-ancres.py --labs
```

`validate-structure --check-urls` ne voit pas ce défaut : il contrôle le code
HTTP de la page, pas le fragment. Une ancre fausse donne un lien qui répond 200
et dépose le lecteur en haut d'un guide de mille lignes.

**Les ancres se lisent, elles ne s'écrivent pas de mémoire.**
`scripts/inventaire-guides.py` les sort du blog, et la règle de slugification
n'est pas celle qu'on devine : les accents sont gardés, la ponctuation
supprimée sans séparateur.

### Un tutoriel qui donne la solution

Le `README.md` enseigne le mécanisme sur un **exemple neutre**, aux noms
étrangers au challenge. Aucun de ses blocs ne doit se copier-coller dans
`challenge/work`.

### Une sortie de commande reconstituée

Toute sortie affichée à l'apprenant est **capturée d'une exécution réelle**.
Cette règle a servi deux fois sur la seule première page du catalogue : le
nombre de couches d'une image de démonstration était faux, et le message
d'erreur de Docker quatre fois plus court que le vrai.

### Un emoji ou un tiret cadratin

Interdits dans ce que l'apprenant lit : scénarios, README, indices, messages
d'assertion. Un hook le vérifie.

## Trois affirmations à ne jamais reproduire

Elles viennent de l'ancien dépôt, et `AUDIT.md` les documente.

- **« Alpine ne contient aucune vulnérabilité »**. Un scan dit ce que sa base
  connaît, à cet instant, des paquets qu'il a su identifier. Un lab de scan
  doit faire constater qu'un résultat est un **état daté**, et sa fixture doit
  être maîtrisée : ne dépendez jamais du fait qu'une image publique soit encore
  vulnérable demain.
- **« Utilisateur non-root (optionnel) »**. Un conteneur en root partage l'UID 0
  avec l'hôte. Faites **échouer** un cas où root nuit, ne vérifiez pas un UID.
- **Un volume NFS sur `127.0.0.1`** dans un exercice « facultatif » qui suppose
  un serveur que rien n'installe.

## Le choix du runtime

`shell` par défaut : le lab se joue sur le poste de l'apprenant, avec son
moteur. Personne ne doit provisionner une machine pour jouer un lab de
fondations.

`vm` seulement quand le lab touche au **démon**, au **noyau** ou à **plusieurs
hôtes** : `daemon.json`, rootless, seccomp, AppArmor, pare-feu, registry TLS,
disque saturé, contexts distants, Swarm.

Et **ne prétendez jamais** avoir validé AppArmor ou seccomp dans un
environnement qui ne les applique pas.

## Avant d'ouvrir une pull request

```bash
pre-commit run --all-files                      # les hooks, étape commit
pre-commit run --all-files --hook-stage pre-push
python3 scripts/valider-labs.py --lab <id>      # 0 puis 100, sans trace
```

Les deux premiers sont mécaniques et ne disent **rien** de la justesse de votre
lab. Seul le troisième l'établit.

## Les commits

Messages en français, sujet factuel qui dit **ce qui a changé et pourquoi**,
sans préfixe conventionnel. Le corps raconte ce qui a été **mesuré**, y compris
les mesures jetées en route : elles valent souvent plus que le résultat.

## Un défaut du moteur n'est pas un défaut du catalogue

dsoxlab vit dans [son propre dépôt](https://github.com/stephrobert/dsoxlab).
Une limite de la CLI devient une issue là-bas, jamais un contournement ici.

## Signaler une erreur dans un guide du blog

Un lab qui contredit sa leçon jumelée a trouvé quelque chose. Cela remonte au
blog, pas ici : ouvrez une issue avec le fichier, la section, ce que le guide
dit, ce qui est vrai, et la commande qui le montre.
