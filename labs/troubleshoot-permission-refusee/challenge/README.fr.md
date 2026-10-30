# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. **Trois conteneurs
butent sur un refus d'accès**, et les trois causes n'ont rien à voir :

```text
perm-a            n'écrit pas dans /ref
perm-b            n'écrit pas dans /donnees
perm-c            n'a pas démarré
temoin-sans-bit   n'a pas démarré non plus, pour la même raison
```

**Commencez par essayer les deux écritures vous-même**, et comparez les deux
messages. Ils ne disent pas la même chose, et c'est toute la clé du diagnostic.

Les trois premières réponses vont dans `/opt/lab-permission/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

## 1. Ce que l'inspection déclare du montage de `perm-b`

À la ligne `rw_b=`.

C'est la réponse qui porte le lab. Les deux premiers conteneurs butent sur un
refus d'écriture, et les deux messages diffèrent déjà : l'un parle d'un
**système de fichiers en lecture seule**, l'autre d'une **permission refusée**.

Le premier accuse le **montage**. Le second dit que le montage autorise
l'écriture, et que ce sont les **droits** qui refusent. L'inspection du
conteneur sépare les deux cas en un mot, et c'est ce mot qu'on vous demande.

## 2. L'uid sous lequel `perm-b` tourne

À la ligne `uid_b=`.

Un conteneur ne tourne pas forcément en root, et quand il tourne sous un uid
applicatif, les droits du répertoire monté le concernent comme n'importe quel
utilisateur du système. Le conteneur sait répondre lui-même.

## 3. Le code de sortie de `temoin-sans-bit`

À la ligne `code_c=`.

C'est le code du fichier **trouvé mais non exécutable**. La cause est dans le
mode du script, qui vient de l'hôte : **un montage n'en change jamais aucun**.

**Ne réparez pas `temoin-sans-bit`** : il reste en panne pour que son code soit
lisible jusqu'au bout. Un conteneur réparé ne porte plus le code qu'on demande,
et un contrôle vérifie qu'il est resté en l'état.

## 4. Réparez les trois, sans passer root

```text
perm-a   doit pouvoir écrire dans /ref
perm-b   doit pouvoir écrire dans /donnees, SANS être root
perm-c   doit TOURNER, et avoir produit sa trace
```

Trois gestes différents, et c'est tout le lab :

- un **montage** ne se change pas sur un conteneur existant ;
- les **droits** d'un répertoire s'alignent sur le groupe du conteneur, comme le
  lab sur les permissions l'a montré. Repasser en root réglerait le symptôme, et
  le contrôle le refuse expressément ;
- un **mode de fichier** se corrige sur l'hôte, puisque le montage ne le change
  pas, et le conteneur se relance ensuite. Dans cet ordre : l'inverse relancerait
  un conteneur qui échouerait pour la même raison.

Chaque réparation est éprouvée par l'**effet** : une écriture réelle pour les
deux premières, la trace du script pour la troisième.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les valeurs se trouvent de plusieurs façons, et
les trois réparations se font par n'importe quel moyen qui produise l'effet
attendu, root excepté pour la deuxième.
