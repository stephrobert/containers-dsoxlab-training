# Terminer une transaction HTTP avant l'arrêt

La leçon arrête une base proprement et mesure un arrêt forcé. Ce cours démonte
les pièces une par une : un lanceur qui garde le signal pour lui, un `--init`
qui ne suffit pas, une transaction interrompue, un dossier sans droit
d'écriture, et un fichier écrit à moitié.

Vous travaillez dans `~/essai-arret`, sur un petit programme et une base SQLite
à vous. Le challenge porte sur le registre de son projet : n'y touchez pas
pendant le cours.

Page associée : [Racine en lecture seule, et arrêt sans perte](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/racine-en-lecture-seule/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-arret-transactionnel
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `essai` lance une
commande, l'arrête, et donne la durée, le code et le journal. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-arret && cd ~/essai-arret
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cat > app.sh <<'EOF'
#!/bin/sh
trap 'echo signal recu; sleep 1; echo travail fini; exit 0' TERM
echo pret
while :; do sleep 1 & wait $!; done
EOF
essai() {
  docker run -d --name essai-app -v "$PWD:/a:ro" $2 "$IMAGE" sh -c "$1; echo suite" > /dev/null; sleep 1
  T=$(date +%s); docker stop --timeout 4 essai-app > /dev/null; T=$(( $(date +%s) - T ))
  [ "$T" -ge 4 ] && T='delai epuise' || T='avant le delai'
  echo "$T, code $(docker inspect essai-app --format '{{.State.ExitCode}}') : $(docker logs essai-app 2>&1 | tr '\n' ' ')"
  docker rm essai-app > /dev/null
}
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📮 Exercice 1 : un lanceur qui garde le signal

Lancez le même programme de trois façons, et arrêtez-le :

```bash
essai 'sh /a/app.sh' ''
essai 'sh /a/app.sh & P=$!; trap "kill -TERM $P" TERM; wait $P; wait $P' ''
essai 'exec sh /a/app.sh' ''
```

```text
delai epuise, code 137 : pret
avant le delai, code 0 : pret signal recu travail fini suite
avant le delai, code 0 : pret signal recu travail fini
```

Le premier lanceur reçoit le signal et n'en fait rien : le programme est tué à
la fin du délai, code 137. Le deuxième le transmet, puis attend la fin. Le
troisième disparaît : `exec` met le programme à sa place.

## 🩹 Exercice 2 : un --init qui ne suffit pas

Ajoutez `--init` au premier lanceur, puis demandez un signal depuis l'intérieur
:

```bash
essai 'sh /a/app.sh' --init
docker run --rm "$IMAGE" sh -c 'kill -9 $$; echo toujours la'
```

```text
avant le delai, code 143 : pret
toujours la
```

L'arrêt est rapide, et le programme n'a rien vu : `--init` transmet le signal
au lanceur, qui meurt, et le conteneur avec lui. Un arrêt rapide n'est pas un
arrêt propre ; cherchez la trace du programme. La seconde commande montre que
le processus 1 ignore même un `kill -9` venu de l'intérieur.

## 🧾 Exercice 3 : une transaction interrompue

Validez une écriture, laissez-en une ouverte, puis tuez celle-ci :

```bash
cat > ecrit.py <<'EOF'
import sqlite3, sys, time
c = sqlite3.connect("base.db", isolation_level=None, timeout=1)
c.execute("create table if not exists t(x)")
c.execute("begin")
c.execute("insert into t values (?)", (sys.argv[1],))
if sys.argv[2] == "valide":
    c.execute("commit")
else:
    time.sleep(60)
EOF
lit() { python3 -c 'import sqlite3; print([r[0] for r in sqlite3.connect("base.db").execute("select x from t")])'; }
python3 ecrit.py un valide
python3 ecrit.py deux attend & P=$!
sleep 1; ls base.db*; lit
python3 ecrit.py trois valide 2>&1 | tail -1
{ kill -9 $P; wait $P; } 2> /dev/null
python3 ecrit.py quatre valide; lit; ls base.db*
```

```text
base.db
base.db-journal
['un']
sqlite3.OperationalError: database is locked
['un', 'quatre']
base.db
```

Tant que la transaction est ouverte, personne ne voit sa ligne et personne
d'autre n'écrit : `database is locked`. Après le `kill -9`, elle est annulée et
le reste est intact. Le fichier `-journal` sert à cette annulation : ne le
supprimez jamais à la main.

## 🔒 Exercice 4 : un dossier sans droit d'écriture

Rendez le dossier non inscriptible, puis le fichier seul :

```bash
chmod 555 .
python3 ecrit.py cinq valide 2>&1 | tail -1; lit
chmod 755 . && chmod 444 base.db
python3 ecrit.py six valide 2>&1 | tail -1
chmod 644 base.db && python3 ecrit.py sept valide && lit
```

```text
sqlite3.OperationalError: attempt to write a readonly database
['un', 'quatre']
sqlite3.OperationalError: attempt to write a readonly database
['un', 'quatre', 'sept']
```

Le même message dans les deux cas. Le fichier était inscriptible la première
fois, mais SQLite doit créer son journal à côté : il lui faut aussi le dossier.
Pour un service non root, donnez-lui le dossier **et** les fichiers déjà
présents.

## ✂️ Exercice 5 : un fichier écrit à moitié

Tuez un conteneur qui écrit directement son résultat, puis un autre qui passe
par un fichier provisoire :

```bash
mkdir -m 777 sortie
LENT='i=0; while [ $i -lt 60 ]; do echo $i; i=$((i+1)); sleep 0.1; done'
docker run -d --name essai-direct -v "$PWD/sortie:/s" "$IMAGE" sh -c "{ $LENT; } > /s/direct" > /dev/null
docker run -d --name essai-abri -v "$PWD/sortie:/s" "$IMAGE" sh -c "{ $LENT; } > /s/abri.tmp && mv /s/abri.tmp /s/abri" > /dev/null
sleep 2; docker kill essai-direct essai-abri > /dev/null
[ "$(wc -l < sortie/direct)" -lt 60 ] && echo 'direct : present et incomplet'
[ -e sortie/abri ] || echo 'abri : absent'
docker rm essai-direct essai-abri > /dev/null
```

```text
direct : present et incomplet
abri : absent
```

Le premier laisse un résultat coupé que rien ne distingue d'un bon. Le second
ne laisse que son fichier provisoire : le nom final n'apparaît qu'une fois
l'écriture finie. C'est la même idée qu'une transaction, pour un simple
fichier.

## 🧹 Nettoyage

```bash
cd ~
sudo rm -rf ~/essai-arret/sortie
rm -rf ~/essai-arret
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
dsoxlab reset container-arret-transactionnel
dsoxlab check container-arret-transactionnel
```

```text
╭─ Résultat : container-arret-transactionnel ─╮
│  0 / 100 pts                                │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests            │
╰─────────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un registre à arrêter sans perdre une commande.

```bash
dsoxlab run container-arret-transactionnel
dsoxlab challenge container-arret-transactionnel
```
