# Politique de sécurité

**Langue :** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

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

Ce qui relève de ce signalement : un lab qui ferait exécuter du code non
vérifié, qui laisserait une porte ouverte sur la machine de l'apprenant après
son `clean`, ou qui exfiltrerait quoi que ce soit. Ce qui n'en relève pas : un
Dockerfile de fixture volontairement fautif.

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

Les labs qui ont besoin de modifier le **démon** — `daemon.json`, rootless,
seccomp, AppArmor, pare-feu — ne se jouent pas sur votre poste : ils déclarent
`runtime: vm` et dsoxlab provisionne une machine dédiée. C'est une règle de
conception, pas une recommandation.
