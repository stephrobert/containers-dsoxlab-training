# Mesurer un refus seccomp ciblé

La leçon dérive un profil et mesure ses champs. Ce cours montre comment un
profil trompe celui qui l'a écrit : un fichier que Docker ne relit pas, un
profil accepté qui ne filtre rien, une erreur qui accuse autre chose, un appel
que l'on n'a pas nommé, et un essai sans blocage.

Vous travaillez dans `~/essai-filtre-appels`. Les profils de ce cours
autorisent tout sauf un appel, pour que l'effet se voie : ils ne conviennent à
aucun service. Le challenge porte sur le `worker` de son projet : n'y touchez
pas pendant le cours.

Page associée : [Confiner par profils : seccomp et AppArmor](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/seccomp-et-apparmor/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-seccomp
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `profil` écrit un
profil qui traite les appels nommés, et `essai` lance une commande avec un
profil. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-filtre-appels && cd ~/essai-filtre-appels
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
profil() { printf '{"defaultAction":"SCMP_ACT_ALLOW","syscalls":[{"names":[%s],"action":"%s"%s}]}\n' "$2" "$3" "${4:-}" > "$1"; }
essai() { docker run --rm --network none --security-opt seccomp="$PWD/$1" "$IMAGE" sh -c "$2"; }
profil base.json '"mkdir","mkdirat"' SCMP_ACT_ERRNO
essai base.json 'mkdir /tmp/a'
```

```text
29.9.2
mkdir: can't create directory '/tmp/a': Operation not permitted
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🧊 Exercice 1 : un fichier qui n'est plus relu

Lancez un conteneur, changez son profil sur le disque, puis relancez-le :

```bash
cp base.json vivant.json
docker run -d --init --name essai-appels --security-opt seccomp="$PWD/vivant.json" "$IMAGE" sleep 600 > /dev/null
profil vivant.json '"rmdir"' SCMP_ACT_ERRNO
docker exec essai-appels mkdir /tmp/a
docker restart --timeout 1 essai-appels > /dev/null
docker exec essai-appels mkdir /tmp/a
rm vivant.json && docker restart --timeout 1 essai-appels > /dev/null && docker exec essai-appels mkdir /tmp/a
docker inspect essai-appels --format '{{index .HostConfig.SecurityOpt 0}}' | cut -c1-60
```

```text
mkdir: can't create directory '/tmp/a': Operation not permitted
mkdir: can't create directory '/tmp/a': Operation not permitted
mkdir: can't create directory '/tmp/a': Operation not permitted
seccomp={"defaultAction":"SCMP_ACT_ALLOW","syscalls":[{"name
```

Le contenu du profil est copié dans le conteneur à sa création. Le modifier, ou
même le supprimer, ne change rien : il faut recréer le conteneur. `docker
inspect` montre le profil réellement appliqué, qui peut différer du fichier.

## 🕳️ Exercice 2 : accepté, et ne filtre rien

Faites une faute dans une clé, donnez un profil vide, puis une action inconnue
:

```bash
sed 's/"syscalls"/"syscals"/' base.json > faute.json
essai faute.json 'mkdir /tmp/a; echo "code: $?"'
echo '{}' > vide.json
essai vide.json 'grep Seccomp: /proc/1/status; unshare -U true; echo "unshare: $?"'
profil action.json '"mkdir"' SCMP_ACT_REFUSE
essai action.json true 2>&1 | grep -o 'string .* for seccomp'
```

```text
code: 0
Seccomp:	0
unshare: 0
string SCMP_ACT_REFUSE is not a valid action for seccomp
```

La clé mal écrite est ignorée. Le profil vide est pire : il retire tout filtre,
et `unshare`, que le profil par défaut refuse, passe. Seule l'action inconnue
arrête le lancement. Vérifiez donc deux choses : `Seccomp: 2`, et un essai qui
doit échouer.

## 🎭 Exercice 3 : une erreur qui accuse autre chose

Faites rendre quatre numéros d'erreur au même refus :

```bash
for n in 1 13 28 38; do
  profil erreur.json '"mkdir","mkdirat"' SCMP_ACT_ERRNO ",\"errnoRet\":$n"
  essai erreur.json 'mkdir /tmp/a'
done
```

```text
mkdir: can't create directory '/tmp/a': Operation not permitted
mkdir: can't create directory '/tmp/a': Permission denied
mkdir: can't create directory '/tmp/a': No space left on device
mkdir: can't create directory '/tmp/a': Function not implemented
```

Le même filtre se fait passer pour un droit manquant, un disque plein ou un
noyau trop ancien. Choisissez un numéro que votre programme sait traiter, et
écrivez-le dans la documentation du profil. `Function not implemented` (38) a
un usage honnête : beaucoup de programmes essaient alors un autre appel.

## 🔎 Exercice 4 : un appel que l'on n'a pas nommé

Cherchez l'appel qu'une commande fait vraiment, puis refusez un appel voisin,
puis le bon :

```bash
strace -f -e trace=mkdir,mkdirat mkdir /tmp/essai-trace 2>&1 | grep -oE '^mkdir(at)?' ; rmdir /tmp/essai-trace
profil voisin.json '"mkdirat"' SCMP_ACT_ERRNO
essai voisin.json 'mkdir /tmp/a; echo "voisin: $?"'
profil bon.json '"mkdir"' SCMP_ACT_ERRNO
essai bon.json 'mkdir /tmp/a; echo "bon: $?"'
```

```text
mkdir
voisin: 0
mkdir: can't create directory '/tmp/a': Operation not permitted
bon: 1
```

Une même action a souvent plusieurs appels, et chaque programme choisit le
sien. Un profil qui n'en nomme qu'un laisse passer les autres. `strace` montre
l'appel d'un programme donné ; nommez toute la famille.

## 📓 Exercice 5 : un essai sans blocage

Remplacez le refus par une trace, et lisez le journal du noyau :

```bash
profil trace.json '"mkdir","mkdirat"' SCMP_ACT_LOG
essai trace.json 'mkdir /tmp/a; echo "code: $?"'
sudo dmesg | grep 'type=1326' | grep 'comm="mkdir"' | tail -1 | grep -oE 'exe="[^"]*"|syscall=[0-9]+' | tr '\n' ' '; echo
docker exec --privileged essai-appels mkdir /tmp/b
docker rm -f essai-appels > /dev/null
```

```text
code: 0
exe="/bin/busybox" syscall=83
mkdir: can't create directory '/tmp/b': Operation not permitted
```

`SCMP_ACT_LOG` laisse passer et note le programme et le numéro de l'appel (83
est `mkdir` sur x86_64). C'est la façon de savoir qui serait gêné avant de
refuser. La dernière commande montre que le filtre vaut aussi pour `docker exec
--privileged`.

## 🧹 Nettoyage

```bash
cd ~
rm -rf ~/essai-filtre-appels
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
dsoxlab reset securite-seccomp
dsoxlab check securite-seccomp
```

```text
╭─── Résultat : securite-seccomp ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une seule valeur d'argument à refuser, sans rien
rouvrir.

```bash
dsoxlab run securite-seccomp
dsoxlab challenge securite-seccomp
```
