# Le conteneur a été recréé, et l'historique n'est plus là

## La situation

Un service d'archivage tourne depuis huit mois. Il écrit son historique dans
`/var/lib/donnees`, à l'intérieur du conteneur, et personne ne s'est jamais
posé de question : ça marche.

Un matin, il faut passer à la version suivante de l'image. La procédure est
celle qu'on connaît : on détruit le conteneur, on en relance un neuf. Dix
secondes, et le service est reparti.

Huit mois d'historique ont disparu avec le conteneur.

Ce n'était pas une panne. Un conteneur a une **couche** à lui, en écriture, et
cette couche est détruite avec lui. Elle n'est pas faite pour les données : elle
est faite pour ce qu'on peut perdre. Trois autres endroits existent, et chacun
sert à autre chose.

## L'objectif

Ranger les données là où elles survivent, avant qu'il soit trop tard. Le
conteneur `archive` tourne, et il porte le même défaut :

```text
/var/lib/donnees/historique.log    dans sa couche. IRREMPLAÇABLE.
```

## Avertissement, à lire avant de taper quoi que ce soit

Le contenu de ce fichier est **tiré au hasard** et n'existe **nulle part
ailleurs**. Si vous détruisez le conteneur avant d'en avoir sorti ce fichier, il
est perdu, et il n'y a aucun rattrapage : il faudra rejouer le lab avec
`dsoxlab reset`.

Son empreinte SHA256 est dans `/opt/lab-volumes/historique.sha256`, pour que
vous puissiez vérifier vous-même votre copie.

C'est exactement l'incident que le scénario raconte, et le vivre une fois vaut
mieux que le lire.

## Ce qui est attendu

Recréez `archive` sous le **même** nom, avec les trois montages :

```text
/var/lib/donnees      le volume nommé `coffre-donnees`
/etc/reference        le répertoire /opt/lab-volumes/reference de l'HÔTE,
                      en LECTURE SEULE
/var/cache/travail    un espace en mémoire, qui ne persiste rien
```

1. Le volume est monté sur `/var/lib/donnees`, et le conteneur y voit le
   fichier `marque.txt` que le volume porte déjà.
2. `/etc/reference` vient de l'hôte et l'écriture y est **refusée**.
3. `/var/cache/travail` est un espace en mémoire, et le conteneur peut y
   écrire.
4. `historique.log` se trouve **dans le volume**, avec son contenu d'origine.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce qui est noté

L'**état du moteur**, et chaque montage est mesuré **deux fois** : ce que
l'inspection déclare, et ce que le conteneur peut réellement faire. Les deux
peuvent diverger, et le cas le plus net est la lecture seule, qui se déclare et
dont le refus s'éprouve.

Le quatrième contrôle lit le **volume lui-même**, par un conteneur à part.
Être visible depuis `archive` ne suffirait pas : tant que le fichier n'est que
dans sa couche, il disparaît avec lui, et c'est tout le sujet.

## Une règle à retenir au-delà de ce lab

Un montage **ne s'ajoute pas** à un conteneur existant. C'est la même règle que
pour les ports publiés et pour le réseau : tout ce qui touche à l'enveloppe d'un
conteneur se décide à sa création.
