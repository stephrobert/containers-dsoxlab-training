# Écrire une politique AppArmor qui refuse par défaut

La leçon écrit un profil, compare les modes et lit le journal. Ce cours montre
ce qu'un profil par chemin ne voit pas et comment il vit : un même fichier sous
un autre chemin, un lien dur, un changement appliqué sans redémarrer, un profil
retiré trop tôt, et un refus par omission observé avant d'être appliqué.

Vous travaillez dans `~/essai-chemins`, avec le profil `essai-aa` que vous
chargez et retirez. Le challenge porte sur le profil
`dsoxlab-securite-apparmor` et son `worker` : n'y touchez pas pendant le cours.

Page associée : [Confiner par profils : seccomp et AppArmor](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/seccomp-et-apparmor/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-apparmor
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. Le profil autorise tout
et refuse une lecture. `lit` lance un conteneur sous ce profil. **Gardez le
même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-chemins && cd ~/essai-chemins
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
mkdir notes && echo contenu > notes/secret
cat > profil <<'EOF'
#include <tunables/global>
profile essai-aa flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  network,
  capability,
  file,
  umount,
  signal (receive) peer=runc,
  deny /notes/secret r,
}
EOF
sudo apparmor_parser --skip-cache -a profil
lit() { docker run --rm --network none --security-opt apparmor=essai-aa -v "$PWD/notes:$1" "$IMAGE" sh -c "$2"; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🗺️ Exercice 1 : un même fichier, un autre chemin

Lisez le fichier, puis montez le même dossier ailleurs :

```bash
lit /notes 'cat /notes/secret'
lit /autre 'cat /autre/secret'
lit /notes 'ln -s /notes/secret /tmp/lien; cat /tmp/lien'
```

```text
cat: can't open '/notes/secret': Permission denied
contenu
cat: can't open '/tmp/lien': Permission denied
```

La règle porte sur un chemin vu du conteneur, pas sur le fichier. Monté
ailleurs, il se lit. Un lien symbolique, en revanche, ne trompe pas le noyau :
il juge le chemin d'arrivée. Une règle `deny` sur un chemin dépend donc de
chaque point de montage.

## 🔗 Exercice 2 : un lien dur

Créez un lien dur vers le fichier, et essayez aussi de le renommer et de le
copier :

```bash
lit /notes 'ln /notes/secret /notes/double && cat /notes/double'
lit /notes 'mv /notes/secret /notes/renomme'
lit /notes 'cp /notes/secret /tmp/copie'
sudo rm -f notes/double
```

```text
contenu
mv: can't rename '/notes/secret': Permission denied
cp: can't open '/notes/secret': Permission denied
```

Le renommage et la copie sont refusés, car ils demandent la lecture. Le lien
dur passe : `file,` l'autorise, et il donne au fichier un second nom que la
règle ne cite pas. C'est la limite d'une liste de refus : elle doit prévoir
chaque détour.

## ⚡ Exercice 3 : un changement appliqué sans redémarrer

Lancez un conteneur, retirez la règle et rechargez le profil, puis remettez-la
:

```bash
docker run -d --init --name essai-vie --security-opt apparmor=essai-aa -v "$PWD/notes:/notes" "$IMAGE" sleep 600 > /dev/null
docker exec essai-vie cat /notes/secret
grep -v deny profil > sans-regle
sudo apparmor_parser --skip-cache -r sans-regle && docker exec essai-vie cat /notes/secret
sudo apparmor_parser --skip-cache -r profil && docker exec essai-vie cat /notes/secret
docker exec --privileged essai-vie cat /notes/secret
```

```text
cat: can't open '/notes/secret': Permission denied
contenu
cat: can't open '/notes/secret': Permission denied
cat: can't open '/notes/secret': Permission denied
```

Le rechargement vaut aussitôt pour le conteneur en marche : le même processus a
perdu puis retrouvé un droit. C'est l'inverse de seccomp. Une erreur dans un
profil rechargé touche donc tous les conteneurs qui le portent. La dernière
ligne montre que `--privileged` n'en sort pas.

## 🧨 Exercice 4 : un profil retiré trop tôt

Retirez le profil alors que le conteneur tourne encore :

```bash
sudo apparmor_parser -R profil
docker inspect essai-vie --format '{{.State.Status}} {{.AppArmorProfile}}'
cat "/proc/$(docker inspect essai-vie --format '{{.State.Pid}}')/attr/current"
docker exec essai-vie true 2>&1 | grep -o 'failed to apply profile'
docker restart --timeout 1 essai-vie 2>&1 | grep -o 'unable to apply apparmor profile'
docker rm -f essai-vie > /dev/null
```

```text
running essai-aa
unconfined
failed to apply profile
unable to apply apparmor profile
```

`docker inspect` affiche toujours le profil, alors que le noyau ne l'applique
plus : le processus en marche n'est plus confiné. On ne peut plus entrer dans
le conteneur, ni le redémarrer. Retirez un profil après le dernier conteneur
qui l'emploie, et croyez le noyau plutôt que `inspect`.

## 📓 Exercice 5 : observer avant d'appliquer

Chargez en `complain` un profil qui ne nomme pas le fichier, et lisez ce que le
noyau a noté :

```bash
sed -e 's/mediate_deleted/mediate_deleted,complain/' -e '/deny/d' -e 's#  file,#  /notes/ r,\n  /{,usr/}bin/* rix,\n  /{,usr/}lib/** mr,#' profil > observe
sudo apparmor_parser --skip-cache -a observe
lit /notes 'cat /notes/secret /proc/1/attr/current'
sudo dmesg | grep 'profile="essai-aa"' | grep 'name="/notes/secret"' | tail -1 | grep -oE 'apparmor="[A-Z]+"|operation="[a-z]+"|requested_mask="[a-z]+"' | tr '\n' ' '; echo
sed 's/,complain//' observe > applique
sudo apparmor_parser --skip-cache -r applique
lit /notes 'cat /notes/secret'
sudo apparmor_parser -R applique
```

```text
contenu
essai-aa (complain)
apparmor="ALLOWED" operation="open" requested_mask="r"
cat: can't open '/notes/secret': Permission denied
```

En `complain`, la lecture passe et le noyau note `ALLOWED` : c'est ce qu'il
aurait refusé. En `enforce`, le même profil refuse, sans règle `deny`. Cherchez
donc `ALLOWED` quand vous observez, et `DENIED` quand vous appliquez.

## 🧹 Nettoyage

```bash
cd ~
sudo aa-status | grep -c essai-aa
rm -rf ~/essai-chemins
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset securite-apparmor
dsoxlab check securite-apparmor
```

```text
╭── Résultat : securite-apparmor ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un profil à écrire, qui n'accorde que le nécessaire.

```bash
dsoxlab run securite-apparmor
dsoxlab challenge securite-apparmor
```
