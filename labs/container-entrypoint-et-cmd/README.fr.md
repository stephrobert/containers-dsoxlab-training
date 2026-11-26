# ENTRYPOINT et CMD : lequel vos arguments remplacent-ils ?

La leçon montre ce que vos arguments remplacent. Ce cours montre comment une
image déclare sa commande, et ce qui s'ensuit : deux écritures qui ne
s'exécutent pas pareil, un argument coupé en morceaux, une image fille qui perd
sa commande, un script d'entrée qui oublie de laisser la place, et une commande
ajoutée après coup.

Vous travaillez dans `~/essai-commande`, sur des images `essai-*`. Le challenge
porte sur `img-cmd:1.0` et `img-entrypoint:1.0` : ne les lancez pas pendant le
cours.

Page associée : [Lancer un conteneur Docker et choisir ce qu'il exécute](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cli/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-entrypoint-et-cmd
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `bati` construit une
image depuis des instructions ; `voit` montre ce qu'elle déclare. **Gardez le
même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-commande && cd ~/essai-commande
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
bati() { printf 'ARG IMAGE\nFROM %s\n%s\n' "${3:-\$IMAGE}" "$2" | docker build -q --build-arg IMAGE="$IMAGE" -t "essai-$1" -f - . > /dev/null 2>&1; }
voit() { docker image inspect essai-$1 --format 'entree={{json .Config.Entrypoint}} cmd={{json .Config.Cmd}}'; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## ✍️ Exercice 1 : deux écritures

Déclarez la même commande sous forme de liste, puis sous forme de phrase :

```bash
bati liste 'ENV QUI=monde
CMD ["echo", "bonjour $QUI"]'
bati phrase 'ENV QUI=monde
CMD echo "bonjour $QUI"'
voit liste; docker run --rm essai-liste
voit phrase; docker run --rm essai-phrase
```

```text
entree=null cmd=["echo","bonjour $QUI"]
bonjour $QUI
entree=null cmd=["/bin/sh","-c","echo \"bonjour $QUI\""]
bonjour monde
```

La phrase passe par un shell, qui remplace la variable ; la liste est exécutée
telle quelle. Prenez la liste par défaut, et la phrase seulement quand il faut
un shell.

## ✂️ Exercice 2 : un argument coupé

Passez une phrase à un programme qui compte ses arguments, avec et sans
guillemets, puis trompez-vous dans la liste :

```bash
cat > compte.sh <<'EOF'
#!/bin/sh
echo "$# argument(s) : $1"
EOF
chmod +x compte.sh
bati compte 'COPY compte.sh /compte
ENTRYPOINT ["/compte"]'
docker run --rm essai-compte deux mots
docker run --rm essai-compte 'deux mots'
bati simple "CMD ['echo', 'salut']"
voit simple; docker run --rm essai-simple 2>&1 | head -1
```

```text
2 argument(s) : deux
1 argument(s) : deux mots
entree=null cmd=["/bin/sh","-c","['echo', 'salut']"]
/bin/sh: [echo,: not found
```

Chaque mot est un argument, sauf entre guillemets. La liste demande des
guillemets **doubles** : avec des simples, Docker la prend pour une phrase,
sans rien dire à la construction, et l'erreur n'arrive qu'au lancement.

## 👶 Exercice 3 : une image fille qui perd sa commande

Partez d'une image qui a les deux, et redéfinissez l'un puis l'autre :

```bash
bati mere 'ENTRYPOINT ["echo", "mere"]
CMD ["defaut"]'
bati fille 'ENTRYPOINT ["echo", "fille"]' essai-mere
bati cadette 'CMD ["autre"]' essai-mere
voit mere; docker run --rm essai-mere
voit fille; docker run --rm essai-fille
voit cadette; docker run --rm essai-cadette
```

```text
entree=["echo","mere"] cmd=["defaut"]
mere defaut
entree=["echo","fille"] cmd=null
fille
entree=["echo","mere"] cmd=["autre"]
mere autre
```

Redéfinir l'entrée efface la commande héritée ; redéfinir la commande garde
l'entrée. Si vous changez l'entrée d'une image existante, réécrivez aussi sa
commande.

## 🚪 Exercice 4 : un script d'entrée qui laisse la place

Écrivez deux scripts d'entrée, l'un qui lance la commande, l'autre qui la
remplace :

```bash
printf '#!/bin/sh\necho preparation\n"$@"\necho suite\n' > lance.sh
printf '#!/bin/sh\necho preparation\nexec "$@"\necho suite\n' > place.sh
chmod +x lance.sh place.sh
for s in lance place; do
  bati $s "COPY $s.sh /entree
ENTRYPOINT [\"/entree\"]
CMD [\"sh\", \"-c\", \"echo je suis le processus \$\$; exit 5\"]"
  docker run --rm essai-$s; echo "$s : code $?"
done
```

```text
preparation
je suis le processus 6
suite
lance : code 0
preparation
je suis le processus 1
place : code 5
```

Sans `exec`, la commande est un enfant, le script continue et son code remplace
celui de la commande : l'échec est perdu. Avec `exec`, la commande devient le
processus 1 et son code ressort.

## ➕ Exercice 5 : une commande ajoutée après coup

Entrez dans un conteneur qui a une entrée, puis regardez ce que `create` a
enregistré :

```bash
bati garde 'ENTRYPOINT ["sleep"]
CMD ["600"]'
docker run -d --init --name essai-garde essai-garde > /dev/null
docker exec essai-garde echo 'sans entree'
docker inspect essai-garde --format '{{.Path}} {{.Args}}'
docker create --name essai-court essai-garde 5 > /dev/null
docker inspect essai-court --format '{{.Path}} {{.Args}}'
docker run --rm essai-garde echo bonjour 2>&1 | grep -o "invalid number 'echo'"
docker rm -f essai-garde essai-court > /dev/null
```

```text
sans entree
sleep [600]
sleep [5]
invalid number 'echo'
```

`docker exec` ignore l'entrée de l'image. `inspect` montre la commande
réellement retenue : regardez-la quand un argument produit une erreur étrange,
comme ce `sleep echo bonjour`.

## 🧹 Nettoyage

```bash
cd ~
docker images -q --filter 'reference=essai-*:latest' | sort -u | xargs docker rmi -f > /dev/null
rm -rf ~/essai-commande
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset container-entrypoint-et-cmd
dsoxlab check container-entrypoint-et-cmd
```

```text
╭─ Résultat : container-entrypoint-et-cmd ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests         │
╰──────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux images, quatre conteneurs, et quatre effets à
obtenir.

```bash
dsoxlab run container-entrypoint-et-cmd
dsoxlab challenge container-entrypoint-et-cmd
```
