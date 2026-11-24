# Corréler une requête métier et attribuer la saturation CPU

La leçon suit une requête dans les journaux et lit les compteurs de bridage. Ce
cours ajoute cinq situations : deux flux mêlés, un message écrit dans un
fichier, un journal borné, un journal perdu à la recréation, et un service lent
que personne ne bride.

Vous travaillez dans `~/essai-traces`, sur un projet `essai-traces`. Le
challenge porte sur `/opt/dsoxlab-compose-correlation-et-saturation` : n'y
touchez pas pendant le cours.

Page associée : [Lire les journaux et attribuer une saturation](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/journaux-et-saturation/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-correlation-et-saturation
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Écrivez un service qui parle à trois endroits, et un autre dont le journal est
borné. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-traces && cd ~/essai-traces
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  guichet:
    image: ${IMAGE}
    init: true
    command: ["sh", "-c", "echo demande recue; echo quantite invalide >&2; echo detail > /tmp/appli.log; sleep 600"]
  compteur:
    image: ${IMAGE}
    init: true
    command: ["sh", "-c", "for i in $$(seq 1 3000); do echo ligne $$i; done; sleep 600"]
    logging:
      driver: json-file
      options:
        max-size: "10k"
        max-file: "2"
EOF
docker compose up -d && sleep 3
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔀 Exercice 1 : deux flux mêlés

Lisez le journal de `guichet`, puis séparez ses deux flux :

```bash
docker compose logs --no-log-prefix guichet 2> /dev/null
echo '-- sortie'
docker logs essai-traces-guichet-1 2> /dev/null
echo '-- erreur'
docker logs essai-traces-guichet-1 2>&1 > /dev/null
```

```text
demande recue
quantite invalide
-- sortie
demande recue
-- erreur
quantite invalide
```

`docker compose logs` affiche tout sur sa sortie standard : y rediriger les
erreurs n'enlève rien. `docker logs` rend les deux flux séparés. Pour ne garder
que les erreurs, employez `docker logs`.

## 📁 Exercice 2 : un message écrit dans un fichier

Cherchez le mot `detail` dans le journal, puis faites pointer le fichier vers
la sortie du conteneur :

```bash
docker compose logs guichet | grep -c detail
docker compose exec guichet cat /tmp/appli.log
sed 's|echo detail|ln -s /dev/stdout /tmp/appli.log; echo detail|' compose.yaml > lien.yaml
docker compose -f lien.yaml up -d guichet && sleep 1
docker compose -f lien.yaml logs guichet | grep -c detail
```

```text
0
detail
1
```

Docker ne collecte que la sortie et l'erreur du processus principal. Un fichier
interne lui échappe, et grossit dans la couche d'écriture. Le lien vers
`/dev/stdout` est la méthode qu'emploient plusieurs images officielles.

## ✂️ Exercice 3 : un journal borné

`compteur` a écrit 3 000 lignes. Comptez celles qui restent :

```bash
docker compose logs --no-log-prefix compteur | wc -l
docker compose logs --no-log-prefix compteur | sed -n '1p;$p'
```

```text
131
ligne 2870
ligne 3000
```

Deux fichiers de 10 Ko au plus ne gardent que la fin. Le disque est protégé,
mais une requête ancienne n'est plus là : choisissez la taille d'après la durée
sur laquelle vous voulez pouvoir chercher.

## 🧹 Exercice 4 : un journal perdu

Redémarrez `guichet`, puis recréez-le, et comptez ses messages à chaque fois :

```bash
docker compose restart guichet && sleep 1
docker compose logs guichet | grep -c 'demande recue'
docker compose up -d --force-recreate guichet && sleep 1
docker compose logs guichet | grep -c 'demande recue'
```

```text
2
1
```

Un redémarrage garde le journal, une recréation le supprime avec le conteneur.
Relevez le journal d'un service en panne avant de le recréer.

## 🐌 Exercice 5 : lent, et jamais bridé

Placez trois services sur le même cœur, l'un plafonné, les deux autres libres.
La fonction `mesure` occupe un service trois secondes :

```bash
cat > coeur.yaml <<'EOF'
x-base: &base
  image: ${IMAGE}
  init: true
  cpuset: "0"
  command: sleep 600
services:
  plafonne:
    <<: *base
    cpus: 0.2
  libre:
    <<: *base
  voisin:
    <<: *base
EOF
cat > mesure.sh <<'EOF'
bride() { awk '/nr_throttled/{print $2}' /sys/fs/cgroup/cpu.stat; }
attente() { awk -F'total=' '/some/{print $2}' /sys/fs/cgroup/cpu.pressure; }
b=$(bride); a=$(attente)
timeout 3 sh -c 'while :; do :; done'
echo "bride: $([ $(( $(bride) - b )) -gt 5 ] && echo oui || echo non), attente: $([ $(( $(attente) - a )) -gt 500000 ] && echo oui || echo non)"
EOF
docker compose -p essai-coeur -f coeur.yaml up -d
mesure() { docker compose -p essai-coeur -f coeur.yaml exec -T "$1" sh < mesure.sh 2> /dev/null | grep bride; }
mesure plafonne
mesure libre
docker compose -p essai-coeur -f coeur.yaml exec -d voisin timeout 6 sh -c 'while :; do :; done'
mesure libre
docker compose -p essai-coeur -f coeur.yaml down
```

```text
bride: oui, attente: oui
bride: non, attente: non
bride: non, attente: oui
```

Le service plafonné est bridé et attend. Le service libre, seul, n'attend pas.
Avec un voisin sur le même cœur, il attend sans être bridé : `nr_throttled` ne
compte que les quotas. `cpu.pressure` mesure le temps passé à attendre le
processeur, quelle qu'en soit la cause. Lisez les deux avant d'accuser un
quota.

## 🧹 Nettoyage

```bash
cd ~
docker compose -f ~/essai-traces/compose.yaml down
rm -r ~/essai-traces
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
0
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset compose-correlation-et-saturation
dsoxlab check compose-correlation-et-saturation
```

```text
╭─ Résultat : compose-correlation-et-saturation ─╮
│  0 / 100 pts                                   │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests               │
╰────────────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux composants, une requête à suivre, et un seul
coupable à désigner.

```bash
dsoxlab run compose-correlation-et-saturation
dsoxlab challenge compose-correlation-et-saturation
```
