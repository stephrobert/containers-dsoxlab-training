# Politique de sécurité

**Langue :** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## Versions supportées

`containers-dsoxlab-training` est en développement actif. Les correctifs de
sécurité sont appliqués à la dernière version de la branche `main`.

| Version | Supportée |
| --- | --- |
| dernière (`main`) | oui |
| plus anciennes | non |

## Ce que ce dépôt contient, et ce qu'il ne contient pas

Un catalogue de labs pédagogiques. Aucun service n'est exposé, aucune donnée
d'utilisateur n'est traitée, et rien n'est déployé depuis ici.

**Certains labs posent volontairement un état fautif.** Un `fixtures/` peut
porter un Dockerfile qui tourne en root, un secret dans une variable
d'environnement, une image non épinglée ou un conteneur trop privilégié : c'est
le sujet de l'exercice, et c'est ce que l'apprenant doit corriger. Un scanner
de sécurité qui lit ce dépôt relèvera donc des constats **attendus**.

La distinction est tenue dans l'outillage, pas laissée à la lecture :

| Ce qui est contrôlé | Ce qui ne l'est pas |
| --- | --- |
| les `solution/`, qui donnent l'exemple | les `fixtures/`, qui posent le problème |
| les scripts du dépôt | `challenge/work`, le répertoire de l'apprenant |

## Signaler une vulnérabilité

Pour un défaut qui dépasse le cadre pédagogique, c'est-à-dire qui mettrait en
danger quelqu'un qui joue un lab :

- ouvrez une [advisory privée](https://github.com/stephrobert/containers-dsoxlab-training/security/advisories/new) ;
- ou écrivez à l'auteur du dépôt.

N'ouvrez pas d'issue publique pour cela.

Merci d'inclure :

- une description de la vulnérabilité et de son impact,
- les étapes pour la reproduire (commande, environnement, `docker version`,
  `dsoxlab --version`),
- tout journal ou preuve de concept pertinent.

Nous vous tiendrons informé de l'avancement du correctif et vous créditerons
dans les notes de version si vous le souhaitez.

## Politique de divulgation

Nous pratiquons la divulgation coordonnée et nous engageons sur les délais
suivants, décomptés à partir de la réception de votre signalement :

| Étape | Délai visé |
| --- | --- |
| Accusé de réception de votre signalement | sous **48 heures** |
| Évaluation initiale et qualification de la sévérité | sous **5 jours** |
| Correctif publié, ou plan de remédiation écrit | sous **30 jours** |
| Divulgation publique de la vulnérabilité | sous **90 jours** |

Nous publions l'avis de sécurité dès qu'un correctif est disponible, ou au plus
tard à l'échéance des **90 jours**, selon ce qui arrive en premier. Si une
vulnérabilité est activement exploitée, nous pouvons la divulguer plus tôt pour
protéger les utilisateurs. Si un correctif complexe demande plus de temps, nous
vous prévenons avant l'échéance et convenons d'une nouvelle date avec vous,
plutôt que de la laisser expirer sans rien dire.

## Périmètre

Ce dépôt livre du **contenu de labs** : un contrat `lab.yaml` par lab, des
playbooks Ansible qui posent et retirent l'état de départ, des tests pytest qui
lisent l'état d'un moteur Docker, et des solutions de référence chiffrées, le
tout exécuté par la CLI externe `dsoxlab`.

Les labs qui modifient le **démon** se jouent sur une machine virtuelle jetable
que `dsoxlab provision` crée. Les autres parlent à un moteur Docker, et c'est
là que se trouve la portée réelle de ce dépôt : un test construit des images et
lance des conteneurs.

Parce qu'une partie du matériel pédagogique est volontairement fautive, CodeQL
n'analyse ni `labs/**/fixtures/**` ni `solution/**` : voir
[`.github/codeql/config.yml`](.github/codeql/config.yml), qui expose le
raisonnement. Une alerte qui ne doit jamais être corrigée n'est plus une alerte :
c'est du bruit, et le bruit cache. Ce que le dépôt livre comme **son** outillage,
c'est-à-dire les workflows, les scripts de validation, `conftest.py` et les
tests pytest, reste entièrement analysé, et c'est exactement le périmètre
énuméré ci-dessous.

Sont dans le périmètre :

- un lab qui ferait exécuter du code non vérifié, qui laisserait une porte
  ouverte sur la machine de l'apprenant après son `clean`, ou qui
  exfiltrerait quoi que ce soit ;
- une évasion de conteneur rendue possible par ce qu'un lab demande de lancer,
  au-delà de ce que le lab enseigne ;
- une fuite de secret réel, une clé privée ou un jeton d'API commité par
  erreur ;
- une solution de référence livrée en clair, qui gâche le lab et reste dans
  l'historique ;
- une image référencée sans épinglage par digest dans ce que le dépôt livre
  comme référence.

Ne sont pas dans le périmètre :

- les vulnérabilités du moteur `dsoxlab` lui-même, qui relèvent de
  [son propre dépôt](https://github.com/stephrobert/dsoxlab) ;
- celles de Docker, d'une image de base ou de tout outil tiers, à signaler à
  leurs projets respectifs ;
- un Dockerfile de fixture volontairement fautif, un conteneur trop privilégié
  ou une image non épinglée quand c'est le sujet de l'exercice ;
- un lab qui échoue ou qui note mal : c'est un défaut, il s'ouvre en issue
  publique.

## Un défaut du moteur n'est pas un défaut du catalogue

dsoxlab vit dans [son propre dépôt](https://github.com/stephrobert/dsoxlab).
Une faille dans la CLI s'y signale, puisque c'est elle qui exécute.

## Ce que les labs font sur votre machine

Les labs en `runtime: shell` parlent à **votre** moteur Docker. Ils y
construisent des images et y lancent des conteneurs, et vous devez savoir dans
quelles limites :

- tout objet créé par un test porte le préfixe `dsoxlab-<lab>-`, donc aucun ne
  peut écraser une image ou un volume qui vous appartient ;
- tout objet créé est retiré à la fin, même quand le test échoue ;
- `scripts/valider-labs.py` photographie le moteur avant et après, et un lab
  qui laisse une trace est refusé.

Les labs qui ont besoin de modifier le **démon** (`daemon.json`, rootless,
seccomp, AppArmor, pare-feu) ne se jouent pas sur votre poste : ils déclarent
`runtime: vm` et dsoxlab provisionne une machine dédiée. C'est une règle de
conception, pas une recommandation.
