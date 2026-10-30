# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le conteneur
`archive` **tourne déjà**, et il écrit ses données dans sa propre couche.

```text
/var/lib/donnees/historique.log    dans sa couche. IRREMPLAÇABLE.
```

## Avertissement, à lire avant de taper quoi que ce soit

Le contenu de ce fichier est **tiré au hasard** et n'existe **nulle part
ailleurs**. Si vous détruisez le conteneur avant d'en avoir sorti ce fichier, il
est perdu, et il n'y a aucun rattrapage : il faudra rejouer le lab avec
`dsoxlab reset`.

Son empreinte SHA256 est dans `/opt/lab-volumes/historique.sha256`. Vous pouvez
vérifier votre copie vous-même, et c'est fait pour.

**L'ordre des gestes est la leçon de ce lab.**

## Ce qu'il faut obtenir

Recréez `archive` sous le **même** nom, avec les trois montages.

## 1. Le volume nommé, sur `/var/lib/donnees`

Le volume `coffre-donnees` existe déjà. Montez-le sur `/var/lib/donnees`.

Le contrôle vérifie deux choses : que c'est bien ce volume, nommé, et que le
conteneur y voit le fichier `marque.txt` que le volume porte **déjà**. Ne pas
voir cette marque signifie que le montage n'atterrit pas où on l'attend.

Un volume anonyme survivrait aussi au conteneur, mais personne ne le
retrouverait jamais : le nommer est tout l'intérêt.

## 2. La référence de l'hôte, en lecture seule

Le répertoire `/opt/lab-volumes/reference` de l'**hôte** doit apparaître dans le
conteneur à `/etc/reference`, et l'écriture y être **refusée**.

Un bind mount ne copie rien : il expose. C'est ce qui le rend commode pour
fournir une configuration, et dangereux pour des données, puisque le conteneur
écrit alors directement sur l'hôte.

Le contrôle mesure la déclaration **et** éprouve le refus : une déclaration
n'est pas une preuve.

## 3. L'espace de travail, en mémoire

`/var/cache/travail` doit être un espace en **mémoire**, et le conteneur doit
pouvoir y écrire.

C'est le montage qu'on oublie, et celui qui évite une classe entière de
problèmes : un espace de travail n'a pas à survivre, ni à être sauvegardé, ni à
remplir le disque, ni à traîner après le conteneur.

## 4. L'historique, dans le volume et intact

`historique.log` doit se trouver **dans le volume**, avec son contenu d'origine.

Le contrôle lit le **volume lui-même**, par un conteneur à part. Être visible
depuis `archive` ne suffit pas : tant que le fichier n'est que dans sa couche,
il disparaît avec lui.

Et il est noté sur son **empreinte** : un fichier recréé à la main aurait le bon
nom et pas le bon contenu.

## Une règle à retenir au-delà de ce lab

Un montage **ne s'ajoute pas** à un conteneur existant. C'est la même règle que
pour les ports publiés et pour le réseau : tout ce qui touche à l'enveloppe d'un
conteneur se décide à sa création.

## Ce qui n'est pas noté

La commande que vous avez tapée. Le fichier peut sortir de plusieurs façons et
entrer dans le volume de plusieurs façons. Seul l'état compte.
