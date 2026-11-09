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

## [Unreleased]

### Ajouté

- **`images-tester-le-contrat` (C19, niveau c5).** L'apprenant écrit un script de
  tests extérieur, `tester-contrat.sh`, qui accepte une image correcte et refuse
  des images cassées de natures différentes. Ce qui est noté est le script, joué
  contre un jeu d'images : une image correcte dont l'apprenant part, un ancien
  build que l'énoncé nomme, et sept images cassées que les contrôles construisent
  eux-mêmes au moment de noter (dossier de données à root, erreur signalée avec
  le code 0, variable obligatoire non vérifiée, processus en root, écriture hors
  du dossier de données, SIGTERM ignoré, compteur perdu à l'arrêt). Six contrôles
  de poids égal ; chaque refus ne compte que si le même script accepte l'image
  correcte, si bien qu'un script qui rend toujours 0 ou toujours 1 obtient zéro.
  Attesté dans les deux sens sur Docker 29.9.2.

- **`docker-mettre-a-jour-le-moteur` (C35c, niveau c6).** Le moteur passe de 29.8.2
  à 29.9.2 exactement sur un hôte qui porte un service témoin. Cinq contrôles sur
  l'état final : la version exacte (et non le candidat du dépôt, 29.9.3), les six
  paquets toujours retenus, `live-restore` actif avec les options de journal
  d'origine conservées, le témoin jamais relancé (processus, heure de démarrage,
  compteur de battements ininterrompu) et sa donnée intacte. La montée est notée,
  le retour arrière ne l'est pas. Le setup ramène le moteur en 29.8.2 et le
  cleanup rend au catalogue le 29.9.2, six paquets retenus, sans `daemon.json`.

- **Un garde-fou sur les exigences critiques**
  (`tests/test_exigence_critique_declaree.py`, câblé en hook). Une promesse
  « aucun total ne compense » écrite dans un énoncé doit avoir sa déclaration
  `exam_blocking_checks`, sinon le moteur ne l'applique pas et l'épreuve est
  reçue avec son exigence critique en échec. Il refuse aussi un nom déclaré
  qui ne correspond à aucun test, parce qu'un test renommé désarmerait
  l'exigence en silence. Il porte un cas qui l'éprouve lui-même, sur un lab
  fabriqué pour échouer.

- **Les quatorze épreuves déclarent leur contrôle bloquant.** dsoxlab 0.7.0
  sait le faire respecter : un échec sur ce contrôle refuse l'épreuve quel que
  soit le total. Mesuré sur les quatorze, avec leur seul contrôle bloquant en
  échec : toutes recalées ; au même score avec un échec ordinaire : toutes
  reçues, sauf les deux dont le score passe sous le seuil.

- **Neuf épreuves de fin de module** portent le catalogue à 90 labs, et le
  nombre d'épreuves à douze : mettre un service en marche, relier deux
  conteneurs, remettre trois conteneurs en service, livrer une première image,
  fiabiliser une stack, contenir un conteneur gourmand, reprendre un hôte
  Docker, durcir sans casser, et reconstruire une image pour deux
  architectures. Chacune porte cinq contrôles de poids égal, un seuil de 75,
  quatre indices payants et une exigence critique qu'aucun total ne compense.
  Toutes attestées le 2026-11-02 sur Docker 29.9.2, magasin containerd.
- **Un contrôle de l'épinglage des versions** (`tests/test_paquets_epingles.py`,
  câblé en hook) : il exige que `infra/bootstrap.yaml` déclare une version
  exacte pour les cinq paquets décisifs, qu'il les mette en `hold`, et que
  la version ne soit recopiée dans aucun `setup.yaml`. Les 75 setups
  installent `docker-ce` en `state: present`, et c'est volontaire : la valeur
  vit à un seul endroit, parce qu'une valeur qu'il faut penser à recopier
  finit toujours par mentir. Les quatre contrôles ont été éprouvés par
  sabotage, et chacun échoue quand il doit échouer.

### Modifié

- **`securite-capabilities` enseigne une exception réelle.** Il exigeait
  `NET_BIND_SERVICE`, qui n'existe pas sous Docker : mesuré sur Engine 29.9.2, un
  conteneur sans aucune capability écoute sur le port 80, parce que le moteur pose
  `net.ipv4.ip_unprivileged_port_start=0` dans son espace de noms réseau. Le lab
  recrée désormais un lanceur de travaux qui s'arrête au démarrage quand toutes
  les capabilities sont retirées (son `chroot` est refusé) et en demande une seule
  en retour, `SYS_CHROOT`. Trois contrôles : l'ensemble déclaré et l'absence de
  mode privilégié, le masque effectif `0x40000` avec le rapport du lanceur
  lui-même, et un vrai changement de propriétaire qui doit échouer. Même
  identifiant, nouveau titre.

- **Trois `doc_url` suivent les leçons réécrites.** `secrets-au-runtime`,
  `docker-contexte-ssh` et `docker-configurer-le-demon` visent désormais la section
  `#mettre-en-pratique` de leur page, la forme des autres labs du catalogue.

- **Le contrôle des ancres de `doc_url` a désormais trois issues, au lieu de
  deux** (`scripts/verifier-ancres.py`, test
  `tests/test_ancres_trois_issues.py` câblé en hook). Il interroge la
  production du site, alors que la vérité d'un `doc_url` est dans la source,
  à laquelle la CI de ce dépôt n'a pas accès. Mesuré le 2026-11-03 en croisant
  les deux, lien par lien, sur les 91 `doc_url` des labs : 41 verts,
  **50 rouges, dont 44 justes à la source** et 6 visant des pages en brouillon.
  Soit **zéro dette réelle du catalogue sur 50 rouges**, et pourtant une CI
  rouge en permanence, dont les PR étaient fusionnées par-dessus. Un contrôle
  qu'on fusionne par-dessus ne contrôle plus rien. Désormais une page
  injoignable ne conclut plus au rouge (c'est `unknown` au sens de
  `dsoxlab doctor` : affiché, jamais tu, et `--strict` lui rend son propre code
  de sortie `10`), et une ancre juste à la source mais pas encore déployée se
  déclare dans `scripts/ancres-en-attente.yml`, nommée, datée et motivée,
  plutôt que tolérée en silence. Ce qui empêche ce fichier de devenir un
  dépotoir : le contrôle **échoue** sur une entrée qui n'a plus d'objet, parce
  que l'ancre résout désormais ou qu'aucun `doc_url` ne la porte plus. Onze
  entrées à l'ouverture, toutes mesurées justes à la source.

- **`epreuve-exposer-sans-exposer-sa-base` est recentrée sur son module.** Quatre de
  ses cinq contrôles redisaient le lab d'une leçon antérieure, et le troisième
  enseignement du module, l'isolement, n'était mesuré nulle part dans le
  catalogue. Elle note désormais la publication sur une interface choisie, un
  **alias** de service distinct du nom du conteneur, un réseau **sans issue**,
  l'absence de port publié sur la base, et la requête métier qui aboutit
  malgré l'isolement. Nouveau titre : « Épreuve : exposer une application sans
  exposer sa base ».

- **`epreuve-remettre-une-stack-en-service` est réécrite.** Elle exigeait une
  sonde de santé et un `depends_on: service_completed_successfully`, tous deux
  enseignés au module suivant. La pile devient un frontal et un service de
  données joints **par leur nom de service**, et le frontal fourni réessaie son
  amont : l'ordre de démarrage est indifférent, donc rien n'est emprunté au
  module suivant.

- **`compose-secrets` fait faire la rotation à l'apprenant.** Le contrôle la
  jouait lui-même, écrivait un jeton neuf, recréait les services et restaurait
  tout : la fiche promettait de « remplacer » un secret et personne ne
  remplaçait rien. Le lab pose désormais la valeur suivante, et le contrôle lit
  l'état final, dont la date de création du conteneur comparée à celle du
  fichier, ce qui attrape les deux pièges de la leçon.

- `reseau-diagnostic-dns` devient `remettre-un-conteneur-en-service`, et
  `compose-capstone` devient `epreuve-remettre-une-stack-en-service`, qui passe
  en `lab_type: challenge` avec un seuil de 75. Les deux attestations ont été
  **retirées** du relevé plutôt que renommées : elle est indexée par
  identifiant, et la renommer ferait passer pour attestée une mesure faite sur
  un autre lab. Les deux labs ont été réattestés sous leur nouveau nom.
- Dix-neuf `doc_url` repointés sur les pages et les ancres qui existent, chaque
  cible vérifiée sur le disque du site avant écriture.
- La promesse d'un fil rouge FastAPI est retirée des deux `meta` : le plan de
  formation ne la prévoit plus.

### Corrigé

- **255 références d'image portaient un digest sans leur tag**, dans 75 labs
  (`setup.yaml` et `cleanup.yaml`), dont **246 `alpine`** épinglées sur le
  digest de `:latest`. Elles étaient reproductibles et pourtant illisibles :
  rien ne disait qu'il s'agissait d'**Alpine 3.24.3**, et le relever a demandé
  un `docker run` sur la VM pour une information qui devrait se lire dans le
  fichier. `LABS-A-ECRIRE.md` exige depuis le 2026-10-29 la forme
  `image:tag@sha256:…` ; `tests/test_images_epinglees.py` ne le vérifiait pas,
  parce qu'il faisait `if "@sha256:" in ref: continue` et acceptait donc toute
  référence à digest. Chaque tag a été **relevé** par
  `docker buildx imagetools inspect` et porte exactement le digest déjà écrit :
  `alpine:3.24.3`, `debian:13`, `debian:13-slim`, `hello-world:latest`. **Aucune
  image ne change**, Docker ignorant le tag dès qu'un digest est présent. Une
  seule référence reste sans tag, `cesanta/docker_auth`, dont le digest n'est
  porté par aucun tag publié et que la ligne **supprime** au lieu de le tirer :
  elle porte le marqueur du dépôt avec sa raison.
- **Le contrôle d'épinglage a désormais deux volets, de périmètres différents à
  dessein.** Celui des références *sans digest* s'en tient à `docker pull`,
  `FROM` et `image:`, parce qu'ailleurs la position de l'image dépend des
  options et qu'un nom de **conteneur** y serait pris pour une image. Celui du
  *digest sans tag* cherche **partout**, la forme `nom@sha256:` étant sans
  ambiguïté. Éprouvé dans les deux sens, marqueur compris, et vérifié capable
  de refuser : en retirant le tag d'une seule référence d'un vrai lab, le
  contrôle le rejette, puis redevient vert une fois restauré.

- **`buildkit-secret-de-build` exigeait deux fois que le secret reste hors du
  contexte de build, et aucun test ne le mesurait.** Ses trois contrôles
  inspectaient l'image, configuration, historique et couches ; or un fichier
  présent dans le contexte mais jamais `COPY` n'entre dans aucune couche.
  **L'exigence était donc invisible, et l'apprenant la croyait notée** : copier
  `depot.token` dans `appli/` puis le passer par
  `--secret id=depot,src=./depot.token` donnait 100. Un quatrième contrôle lit
  désormais le répertoire de contexte, et y cherche le jeton en clair, en
  base64, ainsi que l'en-tête `Bearer` construit sous ses deux formes, parce
  qu'un secret recopié dans une note ou un script d'aide ne se présente pas
  toujours brut. Il refuse aussi le fichier d'identifiant recopié, même vide,
  et **même exclu par un `.dockerignore`** : une exclusion s'oublie, et le
  secret suit alors l'arborescence. Le critère est ajouté à la mission des deux
  scénarios, car une liste qui énumère ce qui est noté doit le nommer.
- **Le scénario de `buildkit-secret-de-build` laissait l'apprenant sans
  `--load`.** Mesuré le 2026-11-03 sur `docker.lab`, Engine 29.9.2, magasin
  containerd : avec le constructeur `docker-container` que le scénario propose,
  une construction sans `--load` **réussit**, l'image reste absente du magasin
  local, et le `docker run` suivant répond « Unable to find image ... locally »
  puis « pull access denied ... may require `docker login` ». **Dans un lab sur
  les secrets de build, ce message envoie l'apprenant chercher un problème
  d'authentification** là où il lui manque une option de sortie. La solution,
  elle, employait `--load` depuis le début, donc l'attestation restait verte.
  Les deux scénarios nomment désormais l'option et disent pourquoi.

- **`images-multi-architecture` comptait les entrées de l'index publié, et non
  ses variantes.** Son énoncé demandait « exactement deux variantes Linux
  distinctes » ; le test exigeait `len(manifests) == 2`. Mesuré le 2026-11-03
  sur Engine 29.9.2 et Buildx 0.38.1, registre jetable : une poussée
  `--platform linux/amd64,linux/arm64 --push` qui laisse la provenance à son
  défaut produit un index de **quatre** entrées, les deux variantes plus deux
  manifestes d'attestation en `unknown/unknown`, annotés
  `vnd.docker.reference.type=attestation-manifest` ; la même avec
  `--provenance=false` en produit deux. **La solution du lab emploie
  `--provenance=false`, donc son attestation restait verte pendant qu'un
  apprenant suivant la leçon échouait** avec le message « une release exige
  deux manifestes distincts » après en avoir livré deux : le même masquage que
  les sept labs de `terraform-training` en juillet. Le test compte désormais
  les variantes, en écartant une entrée sur deux critères et non l'un ou
  l'autre, l'annotation disant l'intention et la plateforme `unknown` la forme.
  Un témoin du même banc montre que rien d'autre ne change : le digest de la
  variante amd64 de l'index à quatre entrées se tire et s'inspecte à
  l'identique. L'indice 3, qui conduisait vers la stratégie d'assemblage pour
  20 points alors que la leçon ne la place qu'en troisième choix, nomme
  maintenant la voie simple d'abord. Lab réattesté VALIDE le 2026-11-03 sur
  Docker 29.9.2. Défaut relevé par la session du site, qui écrivait la leçon.

- **`epreuve-mettre-un-service-en-marche` ne note plus `docker.socket`.** Le
  contrôle était impassable avec ce que la leçon enseigne :
  `docker.service` porte `Requires=docker.socket`, donc la socket devient
  active d'elle-même mais reste **désactivée**, et `is-enabled` refusait le
  geste exact que la leçon montre.

- **`compose-persistance` n'exige plus de racine en lecture seule**, enseignée
  bien plus loin. Elle se cachait à deux endroits, dont un contrôle qui jouait
  `! touch /tmp/unauthorized` et se lisait comme un cloisonnement : mesuré,
  `/tmp` est en 1777 dans l'image, donc ce `touch` réussit sous n'importe quel
  UID et n'échoue **qu'**avec une racine en lecture seule.

- **La « donnée perdue » de `epreuve-remettre-trois-conteneurs-en-service` se
  perd vraiment.** Son rapport ne portait que deux lignes fixes : un scribe
  détruit puis recréé rendait un fichier identique, et l'exigence critique ne
  mesurait rien. Une référence tirée au hasard y est désormais écrite depuis
  l'hôte, et elle part avec le conteneur.

- **Cinq répertoires de travail appartiennent à l'apprenant.** Ils étaient
  `root:root` en 0755, donc rendre son travail exigeait `sudo` : ces labs
  mesurent Docker et Compose, pas la permission d'écrire un fichier.

- **Quatre `doc_url` et quatre niveaux** repointés sur les pages et les ancres
  qui existent, vérifiées avant d'y pointer.

- **Toute mention d'outil d'IA retirée** des commits que l'apprenant voit dans
  `git log`, dans deux labs et non un seul.

- `container-ulimits-et-shm` : les deux scénarios annonçaient **1024**
  descripteurs là où le contrôle en exige **256**. Quiconque suivait l'énoncé
  échouait, pendant que l'attestation restait verte puisque la solution posait
  256. Et tout le discours sur une valeur « qui surprend par sa taille » était
  un vestige de Docker 26 : mesuré sur 29.9.2, `ulimit -n` vaut 1024, et c'est
  l'écart avec le plafond dur de 524288 qui est instructif.
- `internes-cgroups-v2`, `container-limite-cpu` et `container-ulimits-et-shm`
  affirmaient qu'il faut être root pour lire les fichiers d'un cgroup. Mesuré
  depuis un compte ordinaire sans `sudo` : les six fichiers se lisent, zéro
  refus. Les **écrire** demande un privilège, et c'est ce qui sépare
  l'observation du réglage.
- `registry-tag-contre-digest` opposait « le digest du manifeste » et « l'ID de
  configuration » comme deux identités distinctes. Mesuré sur 29.9.2, magasin
  containerd : `.Id` vaut le digest poussé, et le manifeste servi est un index
  OCI sans clé de configuration. L'énoncé demandait d'éviter une valeur qui
  n'existe pas et qui se trouve être la bonne ; ce qui est contrôlé est la
  référence de démarrage.
- Neuf messages d'assertion des nouvelles épreuves passent en bilingue, et un
  marqueur de tag nu manquant est posé sur la seconde tâche de
  `images-identifier-image`.

### Mesuré

- **un `prune` sans `-a` ne retire pas un volume NOMMÉ** : `docker volume
  prune` et `docker system prune --volumes` laissent intact un volume nommé non
  monté, et seul `docker volume prune -a` le retire. Le moteur le dit lui-même
  dans son avertissement, « anonymous » sans `-a`, « all » avec. Trois textes
  nommaient la mauvaise commande ;

- **Compose 5.6.1 applique `deploy.resources.limits.memory`** : cette forme et
  `mem_limit` donnent toutes deux `HostConfig.Memory = 67108864` pour 64M,
  confirmé par le cgroup. Deux indices affirmaient le contraire ;

- **le constructeur par défaut construit et pousse du multi-plateforme** :
  index à quatre manifestes publié depuis le pilote `docker`, sans
  constructeur dédié. Un indice en exigeait un ;

- **un conteneur sur un réseau interne n'a aucune route par défaut**, là où un
  conteneur ordinaire en a une, et le nom comme l'alias y résolvent quand même.
  Un conteneur rattaché aux deux réseaux garde sa route et résout l'alias :
  sans ce fait, l'épreuve recentrée serait injouable ;

- **`docker cp` fonctionne dans les deux sens sur un conteneur arrêté**, et le
  fichier copié survit à son démarrage.

Faits établis sur Docker 29.9.2, magasin containerd, qui ont changé la
conception de plusieurs labs :

- **les images pendantes n'existent plus** : trois builds sur le même tag puis
  le retrait du tag laissent zéro image pendante, une image sans référence
  étant ramassée aussitôt ;
- **`docker kill` ne déclenche pas la politique de redémarrage** : un conteneur
  sous `unless-stopped` reste `exited`, compteur à zéro, sur dix lectures en
  trente secondes. Le noyau protège par ailleurs le PID 1 d'un namespace contre
  un `kill -9` venu de l'intérieur ;
- **`NET_BIND_SERVICE` ne sert à rien dans un conteneur** : le démon y pose
  `net.ipv4.ip_unprivileged_port_start = 0`, donc un conteneur sans aucune
  capability écoute sur le port 80 ;
- **`docker run --platform` n'honore pas la plateforme** si une image locale
  correspond déjà à la référence : il faut un `docker pull --platform`
  explicite, sans quoi l'autre architecture n'est jamais exécutée ;
- **un index publié par buildx porte quatre manifestes et non deux**, à cause
  des attestations de provenance, qui se présentent comme des plateformes
  `unknown` ;
- **`--build-arg` laisse un secret dans l'historique** (deux occurrences) là où
  `--mount=type=secret` n'en laisse aucune, ni dans l'historique ni dans les
  couches ;
- **l'image `registry:3.1.2` déclare un `VOLUME`** : chaque conteneur de
  registre crée un volume anonyme, et `docker rm` sans `-v` le laisse.

### Ajouté

- Six labs portent le catalogue à 77 : arrêt transactionnel, exécution
  AMD64/ARM64 (QEMU dans la VM pour ARM64), ACL de registre TLS, identité de
  signature approuvée, saturation CPU corrélée et réparation ciblée de
  pare-feu. Ils suivent l'ordre pédagogique du catalogue.
- Le diagnostic débutant avec conservation des données et l'arrêt
  transactionnel suivent les volumes et permissions UID/GID. La persistance
  conserve les droits non-root et les refus après recréation ; les essais
  CPU, OOM et limites de processus préservent des reçus applicatifs frais.
- Une seconde VM permet les pulls sur client vierge, la restauration
  applicative et la promotion d'un artefact sans reconstruction. Le bootstrap
  installe le socle Docker ; les rôles runtime sont rejoués et photographiés.
- La validation stricte `--double-passage` exige `0/plein/0/plein/propre`.
  La relecture respecte `--lab` ; une attestation historique ne prouve pas
  le second passage strict.

- Neuf labs complétés sur `chantier/labs-restants` : `buildkit-cache-monte`,
  `buildkit-secret-de-build`, `registry-tag-push-pull`,
  `registry-tag-contre-digest`, `images-epingler-par-digest`,
  `registry-locale-tls`, `registry-authentification`, `registry-air-gap`
  et `compose-premiere-stack`, avec énoncés et indices bilingues,
  solutions de référence chiffrées et attestations runtime.
- La confiance des registres est mesurée par de vrais refus après retrait de
  la CA. Les contrôles air-gap refusent des couches absentes malgré un cache
  Docker chaud et une somme recalculée. Compose recrée ses deux services.
- Huit autres labs Compose couvrent résolution des variables, isolation réseau,
  persistance, migration ponctuelle, secrets, dépendances de santé, budgets
  de ressources et environnements multiples. Chacun porte des textes bilingues,
  une solution chiffrée et un cycle VM mesuré 0 → 100 → 0.
  Les essais vérifient l'isolation par IP, les nouvelles écritures persistantes,
  les refus de démarrage après tâche échouée ou disponibilité absente, la rotation
  du jeton, les cgroups effectifs et la recréation indépendante des environnements.
- Sept derniers labs d'administration et de sécurité couvrent les valeurs par
  défaut du démon Docker, les contextes SSH, la rotation des journaux par
  conteneur, le retrait du privilège du groupe Docker, le mode rootless, les
  montages de socket dangereux et un proxy d'API à privilèges minimaux. Chacun
  comporte des consignes bilingues, une solution chiffrée et une attestation VM
  avec nettoyage vérifié.
- Le lab de sauvegarde PostgreSQL a désormais une solution de référence chiffrée
  et des tests qui restaurent indépendamment une sauvegarde personnalisée puis
  comparent les lignes réelles.
- Les 71 labs du catalogue ont maintenant un verdict `VALIDE` dans
  `validation-labs.json` ; le capstone final et la nouvelle révision du proxy
  de socket ont réussi leur cycle VM.

### Corrigé

- La validation des labs VM photographie désormais Docker par SSH sur la
  cible réelle, identifiants des images orphelines compris, et non sur le
  poste. Le nettoyage refuse aussi la suppression d'objets préexistants.
  Les nouveaux labs retirent leurs images intermédiaires étiquetées sans
  purge globale. Les attestations antérieures doivent être rejouées avant
  de revendiquer cette garantie renforcée.

## [0.2.3] - 2026-10-23

### Ajouté

- Un verdict ne peut plus être commité avec ce qu'il mesure. Le hook
  `verdicts-et-commun-separes` refuse un commit portant `validation-labs.json`
  à côté de ce que le cycle joue : `challenge/tests/`, `setup.yaml`,
  `cleanup.yaml`, `lab.yaml` d'un lab, et l'outillage partagé. Il est lui-même
  éprouvé, dans les deux sens, par un hook à lui.

  Cela ferme un cas **qu'aucune mesure ne rattrape après coup**. La péremption
  d'un verdict se jugeait en comparant des DATES, et cette comparaison s'est
  trompée dans les deux sens le 2026-10-22 : une correction commitée avec les
  verdicts qu'elle périmait est passée pour saine, et des labs réattestés sur
  une branche sont ressortis « à réattester » après leur fusion en squash,
  contenu inchangé. Quand une pull request squashée retouche un test *après* sa
  campagne, le commit unique porte les deux et le squash a détruit ce qui les
  distinguait. Cela ne se constate pas, donc cela s'empêche.

  L'énoncé reste autorisé à côté d'un relevé : il n'est pas joué par le cycle,
  et l'interdire obligerait à une campagne pour une coquille.

### Corrigé

- `pipelineMustNotLeakSecretsInConfig` est retiré du `.plumber.yaml`, où il
  était déclaré deux fois. Plumber a supprimé ce contrôle et répond « was
  removed and is now ignored: secret detection is no longer part of Plumber;
  remove this block ». Le garder laissait croire que la détection de secrets
  était couverte ici. Elle ne l'est pas, et c'est `detect-private-key` qui s'en
  approche, en hook.

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

- **Le rejeu « 0 avant, 100 après » ne se joue plus en CI, et c'est le coût
  assumé du chiffrement.** Ce cycle pose la solution du formateur sur le
  répertoire de travail : il lui faut le clair, et `.vault-pass` n'est pas sur
  la forge. Les deux étapes concernées se déclarent donc non jouées, par un
  avertissement visible, plutôt que de passer pour un succès.

  Ce qu'on perd est réel et mérite d'être nommé : l'opposabilité de
  `validation-labs.json` ne tient plus à cette CI mais à la campagne locale
  qui l'a produit. C'est désormais la situation des onze autres catalogues de
  la collection, dont aucune CI ne rejoue de lab. Le relevé commité porte
  `images-premiere-image → VALIDE` au 2026-10-01, et c'est lui qui prouve.

  L'autre voie existait, et elle a été écartée : confier `.vault-pass` à un
  secret de dépôt aurait gardé le rejeu, au prix de mettre sur la forge le
  secret qu'aucun catalogue n'y met.

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
