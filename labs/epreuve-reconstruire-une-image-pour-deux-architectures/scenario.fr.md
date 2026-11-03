# Une seule image, quatre exigences, deux architectures

L'image `deux-arch:1.0` marche. Elle pèse environ 200 Mo, son `Dockerfile` tient
en une seule étape, le jeton du dépôt privé y passe par un `ARG`, et elle
n'existe que pour une architecture.

**C'est une épreuve d'enchaînement.** Les quatre gestes ont été vus séparément
dans le parcours ; il s'agit ici de les réunir dans **une seule image**. Une
image légère dont le secret a fui ne vaut rien, et une image propre qui ne sert
qu'une architecture ne se déploie pas.

## Ce qui est attendu à la fin

1. L'image **publiée** ne contient ni le compilateur ni le gestionnaire de
   paquets de l'image de base, et son exécution rend la charge métier.
2. Sa taille reste **sous le seuil** que ce lab a mesuré sur cette machine, en
   construisant lui-même une référence multi-étapes.
3. Le jeton n'apparaît **ni dans les couches ni dans
   `docker history --no-trunc`**. C'est la seule exigence qu'**aucun total ne
   compense** : si le secret fuit, l'épreuve est refusée quel que soit le score.
4. La **dépendance privée** est bien présente dans l'image, ce qui n'est
   possible que si le jeton a **servi**. Retirer le jeton sans s'en servir coûte
   ce contrôle, et lui seul : ce n'est pas une fuite.
5. Le registre du lab, sur `127.0.0.1:15002`, sert un **index** qui porte
   `linux/amd64` **et** `linux/arm64`, et **chacune des deux s'exécute**.
6. Le digest de l'**index** est consigné dans `/opt/lab-deux-arch/digest.txt`,
   sur une seule ligne, sous la forme `sha256:...`.

**L'émulation des architectures étrangères est déjà en place** : ce lab l'a
posée. Vous n'avez pas à l'installer.

L'énoncé complet est aussi sur la machine, dans
`/opt/lab-deux-arch/MISSION.md`.

## Trois précisions pour ne pas chercher au mauvais endroit

**Le binaire peut être compilé statiquement**, et une image dont le binaire est
statique n'a besoin d'aucun système autour de lui : ni compilateur, ni
gestionnaire de paquets, ni shell. C'est la voie qui satisfait la première
exigence sans contorsion, parce que le gestionnaire de paquets d'une image de
base y est toujours présent.

**Le jeton sert à produire la dépendance**, et dans ce lab la dépendance **est**
le condensat du jeton, ses seize premiers caractères. C'est dit franchement : un
vrai dépôt réseau ne changerait rien à ce qui est mesuré, qui est que le secret
ait **servi** et qu'il n'ait pas **fui**.

**L'index publié porte plus de deux entrées.** L'outil de construction y ajoute
ses attestations, qui se présentent comme des plateformes `unknown`. C'est
normal, et le contrôle cherche les deux architectures **parmi** les entrées.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Les contrôles
portent sur **l'image tirée du registre**, et non sur une image locale : publier
sans rien garder en local est la façon normale de faire, et l'épreuve ne doit pas
la punir.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**le jeton lisible dans l'historique fait échouer l'épreuve**, même avec tout le
reste en place. Un `--build-arg` y laisse sa valeur, et quiconque tire l'image la
relit. L'image elle-même a l'air propre, ce qui fait de cette fuite la plus
discrète du métier.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
