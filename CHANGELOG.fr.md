# Journal des changements

**Langue :** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

Ce journal est **daté, et non versionné**, comme celui du catalogue GitHub
Actions. Un numéro de version promet une compatibilité entre deux états d'un
logiciel ; un catalogue de labs n'a rien de tel à promettre, et un apprenant ne
joue jamais « la version 1.2 » d'un lab, il joue celui qui est en ligne.

Ce que la date apporte, elle : savoir **quand** un lab a été éprouvé, avec
quelle version du moteur Docker et dans quel mode de stockage. C'est ce que
`validation-labs.json` enregistre lab par lab, et ce journal le résume.

---

## [0.2.2] - 2026-10-19

### Sécurité

- **La solution du formateur est chiffrée par ansible-vault.** Le
  `Dockerfile` de `images-premiere-image` était commité en clair, dans un
  dépôt public : l'apprenant qui clone avait la réponse du premier lab sous la
  main. Les autres catalogues chiffrent les leurs, et celui-ci ne le faisait
  pas.

  Il passait aussi au travers du contrôle, et ça valait d'être corrigé en
  amont : `dsoxlab validate-structure` ne regardait que six extensions
  (`.yaml`, `.yml`, `.sh`, `.py`, `.bash`, `.txt`), donc un fichier nommé
  `Dockerfile` n'était même pas ouvert. Le moteur contrôle désormais tout
  fichier texte d'un répertoire de solutions, à partir de la 0.5.4.

  `scripts/valider-labs.py` pose la solution par-dessus le répertoire de
  travail, fichier par fichier : il la **déchiffre maintenant à la pose**, par
  `scripts/lecture_solution.py`. Sans quoi `docker build` aurait lu
  « $ANSIBLE_VAULT;1.1;AES256 » comme une instruction, et son erreur aurait
  parlé de syntaxe Dockerfile plutôt que de chiffrement.

  Vérifié sur le comportement : la pose rend le Dockerfile original à l'octet
  près, somme SHA256 comparée avant et après. Les 31 tests du dépôt passent et
  `validate-structure` est vert.

- **`scripts/hooks/hadolint-cible.sh` déchiffre avant d'analyser.** C'était le
  second lecteur du fichier, et le plus discret : hadolint lirait l'en-tête
  vault et son pavé hexadécimal sans y voir une seule instruction, donc il
  rendrait du vert sans avoir rien contrôlé. Il analyse maintenant une copie
  déchiffrée, dont le nom conserve le chemin d'origine pour que ses messages
  restent lisibles.

  En CI, `.vault-pass` n'existe pas, et c'est la convention de toute la
  collection : aucun catalogue ne confie son secret à la forge. Le contrôle
  s'y déclare donc **non joué**, par un avertissement visible dans
  l'interface, au lieu de passer pour un succès. Il se joue chez le formateur,
  qui a le secret. C'est le coût assumé du chiffrement, et il valait d'être
  écrit plutôt que découvert.

  Les deux chemins ont été éprouvés plutôt que supposés : avec le secret,
  hadolint analyse le Dockerfile et rend son `DL3008` ; sans lui, le script
  avertit et sort en 0.

## [0.2.1] - 2026-10-19

### Modifié

- **Chaque `doc_url` pointe désormais `www.stephane-robert.info`.** Le site est
  passé de `blog.` à `www.`, et l'ancien hôte redirige en 301 vers le même
  chemin. Rien n'était cassé : `validate-structure --check-urls` suit les
  redirections, et ce catalogue était vert avant qu'une ligne change. La
  migration est une mise au propre et non une réparation : un `doc_url` doit
  pointer la page, pas dépendre d'une redirection qu'il faudra bien retirer un
  jour.

  Les chemins sont identiques entre les deux hôtes : seul l'hôte a changé. Les
  359 `doc_url` que les catalogues déclarent ont été cherchés dans le dépôt du
  site, hors réseau : ils y existent tous, y compris vingt-trois pages que
  l'ancien hôte rendait en 404.

## 2026-10-01

Ce dépôt naît ce jour, et il remplace
[containers-training](https://github.com/stephrobert/containers-training), qui
reste en place avec ses 168 étoiles et ses 47 forks.

### Kubernetes quitte le catalogue

`03-Kubernetes/` est retiré entièrement : Kubernetes vit dans
`kubernetes-dsoxlab-training`, avec ses labs CKA, CKAD et CKS sur un cluster
kubeadm réel. Deux formations concurrentes sur un même sujet divergent.

`01-Docker-compose/` et `02-Docker-swarm/` partent aussi. Ils ne contenaient
qu'un `.gitkeep`, alors que le README les annonçait comme du contenu. Ils
reviendront comme vrais blocs de formation.

### Les cinq TP deviennent des labs mesurés

Les 1101 lignes de pas-à-pas disparaissent. Elles enseignaient, et elles
enseignaient bien, mais elles ne mesuraient rien : l'apprenant qui recopiait les
blocs arrivait au résultat sans qu'aucun contrôle ne distingue le travail
compris du travail recopié.

Ce qui est repris : l'application FastAPI, qui devient le **fil rouge** du
catalogue, et la progression en quatre images successives. Ce qui est jeté :
le texte, qui doublait le blog, et trois affirmations fausses.

`AUDIT.md` les documente, mesure en main. Les trois plus lourdes :

- « L'image Alpine ne contient à ce jour aucune vulnérabilité ! », suivie de
  « Vérifier la sécurité de l'image avec Trivy ». Un scan dit ce que sa base
  connaît, à cet instant, des paquets qu'il a su identifier ;
- « Utilisateur non-root (optionnel) », seul `USER` des cinq TP ;
- un volume NFS sur `127.0.0.1`, dans une étape « facultative » qui suppose un
  serveur que rien n'installe.

Un quatrième défaut n'était pas soupçonné : le `COPY app/` précédait
l'installation des dépendances, donc une ligne de Python invalidait la couche la
plus coûteuse.

### Le premier lab, éprouvé dans les deux sens

`images-premiere-image` porte sept contrôles, et le dernier est celui qui
compte : il lance l'image avec `--network none` et exige qu'elle réponde quand
même. Une image qui installe ses dépendances au démarrage passe les six autres
et échoue là, comme elle échouerait chez un apprenant hors ligne.

```
avant le travail : 0/7
après la solution : 7/7
après clean et run : 0/7
moteur rendu intact
VALIDE
```

Les dépendances de l'application sont **épinglées et datées** :
`fastapi==0.142.2`, `uvicorn[standard]==0.54.0`, mesurées sur PyPI ce jour. Le
TP d'origine ne les épinglait pas, et la même image reconstruite dans six mois
n'aurait plus porté le même code.

### Deux mesures qui ont changé la conception

**La même image mesure 83 Mio par l'API et 329 Mio par `docker images`.** Un
facteur quatre, parce que le moteur emploie le containerd image store : l'API
rend la taille compressée, celle du registre, et la commande celle du disque.

Trois des cinq labs à transposer sont des labs d'optimisation. Un seuil en
octets écrit dans un test serait donc incompréhensible, puisque l'apprenant lit
l'autre chiffre dans son terminal. `conftest.py` expose les deux lectures, et
les labs comparent des **rapports** entre images mesurées de la même façon.

**Une ancre est acceptée dans `doc_url`**, ce qui rend tenable un jumelage
précis là où les guides sont concentrés : 1095 lignes de guide Swarm pour 18
labs visés, 798 pour les 12 labs Compose.

Mais la règle de slugification du blog ne se devine pas. Un premier slugifieur
tombait juste 26 fois sur 68. La vraie règle garde les accents et supprime la
ponctuation sans séparateur :

```text
'Prérequis'                     -> #prérequis
"Initialisation d'un cluster"   -> #initialisation-dun-cluster
"Qu'est-ce que Docker Swarm ?"  -> #quest-ce-que-docker-swarm-
'Exemple : workers uniquement'  -> #exemple--workers-uniquement
```

Corrigée, elle tombe juste **114 fois sur 114**.

### Le vérificateur qui a rattrapé 44 erreurs

`scripts/verifier-ancres.py`, écrit pour contrôler le backlog, a montré que
**44 des 64 ancres rédigées étaient fausses** : celles tirées de l'inventaire du
blog étaient justes, celles écrites de mémoire étaient inventées, et rien ne les
distinguait à la lecture.

`validate-structure --check-urls` ne voit pas ce défaut : il contrôle le code
HTTP de la page, pas le fragment.

### L'analyse avant le code

`AUDIT.md`, `COVERAGE.md` et `ROADMAP.md` sont livrés avant d'écrire des labs
en série. Ils disent, chiffres en main : 42 guides dans le périmètre, 525
sections, 16 quiz déjà en ligne, et **trois trous** que l'ancien dépôt laissait
béants.

| Compétence | Guides disponibles | Labs d'avant |
| --- | --- | --- |
| distribuer les images | 7 guides, 2 505 lignes | aucun |
| exploiter et dépanner | 3 guides, 2 176 lignes | aucun |
| sécuriser | 3 guides, 1 896 lignes | aucun |

Le backlog compte **89 labs**, répartis en six vagues, dont la vague 2
entièrement jouable sans provisionner une machine.

### Le socle technique

`meta.yml` au contrat v1 de dsoxlab 0.3.0, organisé **par compétence** et non
par fonctionnalité. `conftest.py` avec les primitives Docker. Seize hooks
pre-commit, quatre vérificateurs de catalogue, et un validateur qui photographie
le moteur avant et après chaque lab.

La licence passe de CC BY-SA 4.0 à **CC BY 4.0**, comme les trois autres
catalogues, texte officiel nu : un `LICENSE` précédé d'un encadré n'est pas
détecté par GitHub.

`mise.toml` épingle hadolint, dive, trivy et uv. **Docker n'y est pas** :
`mise ls-remote docker` ne rend rien, et c'est logique. Un démon avec son
service, son groupe et son socket ne s'installe pas en déposant un binaire. Le
catalogue le **vérifie** au lieu de l'installer.

## [0.2.0] - 2026-10-17

### Modifié

- **Le validateur lit le contrat, plus l'encadré du terminal.**
  `scripts/valider-labs.py` lisait le score dans ce que `dsoxlab check`
  *affiche*. Cet encadré est de l'interface : il a changé en dsoxlab 0.4.0 et
  la regex a cessé de trouver quoi que ce soit. Il lit désormais
  `check --json`, qui porte un `schema`, et cette lecture vit dans
  `scripts/verdict_check.py`, **identique dans les douze catalogues**.

- **Trois verdicts, pas deux.** Une exécution dont tous les tests collectés ont
  skippé n'a rien mesuré : elle est **SKIP**, ni verte ni rouge, et reste à
  mesurer. La peindre en rouge accuserait le lab de ce qui manque au poste.
  `--check` sort donc en `10` dans ce cas, contre `1` pour un ROUGE, à l'image
  de `dsoxlab doctor --strict` où 9 se répare et 10 se remesure.

- **Le README prend la structure de référence** commune aux douze catalogues :
  quatorze sections, dans les deux langues. Sept d'entre elles décrivent
  dsoxlab et non le sujet, et sont donc identiques partout.

### Exige

- **dsoxlab 0.4.1 ou plus récent**, qui a introduit le champ `status` de
  `check --json`. Sans lui, le validateur refuse de conclure plutôt que de
  deviner.
