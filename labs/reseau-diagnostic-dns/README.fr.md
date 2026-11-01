# reseau-diagnostic-dns : l'épreuve du parcours réseau

## Ce que cette épreuve éprouve

Le diagnostic, et non une commande. Elle clôt les cinq labs réseau du parcours
et ne réexplique rien : ce qu'il faut savoir y a été enseigné, celle-ci le
mesure.

C'est le seul `lab_type: challenge` de la section, et c'est ce qui autorise son
`exam_passing_score`, fixé à **75**. Les cinq contrôles sont de poids égal ;
le parcours exige séparément la réussite de la conservation critique des données.

## La panne posée, et elle n'est dite nulle part dans l'énoncé

| Faute | Symptôme visible | Ce qu'elle enseigne |
| --- | --- | --- |
| les deux conteneurs sur deux réseaux dédiés **différents** | aucun nom ne résout | deux stacks montées séparément ne se parlent pas |
| l'application cherche `base`, le conteneur s'appelle `catalogue` | le nom attendu ne résout pas, même sur un réseau commun | les alias réseau existent pour ça |
| `catalogue` publie un port sur toutes les interfaces | l'audit le signale | rien ne retire un `-p` sur un conteneur existant |

Les trois sont indépendantes et toutes crédibles. La première est le cas banal
de deux équipes qui déploient chacune de leur côté, ce que le scénario raconte.

## Trois symptômes, une correction

Recréer `catalogue` sur le réseau de `boutique`, avec l'alias et sans
publication. **Un seul geste règle les trois fautes**, et c'est ce qui fait la
valeur de l'épreuve : le diagnostic précède la main.

Corriger au fur et à mesure fonctionne aussi, en trois fois. Les tests notent
l'état, jamais le chemin, donc les deux comptent. Mais l'un enseigne à
diagnostiquer et l'autre à tâtonner.

## Pourquoi le quatrième contrôle exige le vrai nom

Sans lui, **renommer le conteneur en `base` satisferait les trois autres**, et
l'apprenant n'aurait rien appris des alias réseau.

L'exigence figure dans l'énoncé, donc ce n'est pas un piège. Et elle est la
situation réelle : l'application a son nom à elle, écrit dans une configuration
qu'on ne peut pas changer, et l'exploitation garde le sien, celui des journaux
et des inventaires. **Un alias s'ajoute, il ne remplace pas.**

Mesuré sur `docker.lab` le 2026-10-30 : un alias posé sur un réseau laisse le
vrai nom résoudre. Les deux exigences sont donc satisfiables ensemble, et seul
un renommage les oppose.

## Ce que les messages des contrôles disent, et ne disent pas

Un lab guide : son message nomme le geste qui manque. **Un challenge évalue :
son message nomme le symptôme précis et s'arrête là.**

Aucun message de ce fichier ne dit « rattachez le conteneur » ni « posez un
alias ». Les indices sont là pour ça, et ils coûtent des points. C'est la seule
différence d'écriture entre un lab et un challenge de ce dépôt, et elle est
entière.

## Pourquoi résoudre et joindre sont deux contrôles

Leurs causes sont différentes. Un résolveur peut répondre pour une adresse
qu'aucune route n'atteint, ce qui arrive dès qu'un conteneur est sur plusieurs
réseaux.

Les séparer permet au message de nommer la bonne panne. Fusionnés, ils
diraient « ça ne marche pas », ce qui est exactement ce qu'un apprenant sait
déjà en arrivant.

## Pourquoi le premier contrôle vérifie que l'adresse est la bonne

Il ne se contente pas d'une résolution qui aboutit : il vérifie que l'adresse
rendue est bien une adresse que `catalogue` porte.

Un nom qui pointe ailleurs est **pire** que pas de nom du tout : l'application
parlerait à autre chose, et le symptôme deviendrait incompréhensible. C'est un
cas réel dès qu'un nom traîne dans un résolveur.

## Réparation durable et nettoyage borné

Une valeur nouvelle du volume nommé reste visible après remplacement réel
du catalogue, via le chemin applicatif corrigé. Conteneurs, images, réseaux
et volumes portent le label de propriété du lab ; seuls ces objets sont retirés.
Les bases préexistantes restent intactes ; une base introduite est retirée sans
force seulement si inutilisée. Aucun prune réseau/image/builder global :
un objet inutilisé peut appartenir à un autre propriétaire.

## L'état de départ est cassé, et c'est la règle du dépôt

Les cinq contrôles sont faux au départ. Une tâche du setup **vérifie** les
trois fautes avant de rendre la main : les deux noms ne résolvent pas depuis
`boutique`, et le port est bien publié.

## Ce que l'épreuve n'exige pas

Un chemin. Recréer le conteneur, le rattacher puis le détacher, créer un
troisième réseau : tout ce qui aboutit à l'état demandé compte. Les tests ne
nomment d'ailleurs aucun réseau, et ils lisent les adresses du conteneur sur
**tous** ses réseaux.
