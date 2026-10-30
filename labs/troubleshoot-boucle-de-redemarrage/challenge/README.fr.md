# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. **Trois conteneurs
partagent le même défaut**, et ils s'en sortent de trois façons :

```text
appli-plafond    le moteur a RENONCÉ à le relancer
appli-sans-fin   le moteur le relance encore, et encore
appli-saine      tourne, et doit continuer de tourner
```

**Commencez par lire les traces de `appli-sans-fin`.** Elles disent ce qui
manque, et elles le disent autant de fois qu'il y a eu de tentatives.

Les trois premières réponses vont dans `/opt/lab-boucle/reponses.txt`, une ligne
par entrée, sans espace autour du signe égal.

## 1. Combien de fois le moteur a relancé `appli-plafond`

À la ligne `tentatives=`.

Sa politique porte un **plafond** : le moteur relance tant qu'il n'est pas
atteint, puis il renonce. C'est ce qui le distingue de l'autre, dont le compteur
grimpe encore, et c'est pourquoi la question se pose sur lui : sa valeur ne bouge
plus.

Le plafond est déclaré dans sa politique, et le compte des tentatives réellement
faites est ailleurs dans la même inspection.

**Ne réparez pas `appli-plafond`** : un conteneur relancé repart de zéro, sans
compteur ni code de sortie. Un contrôle vérifie qu'il est resté arrêté.

## 2. Le code de sortie de `appli-plafond`

À la ligne `code=`.

C'est le code de la **dernière tentative**, et c'est celui du script lui-même.
Il ne se lit pas dans les traces : les traces disent ce qui manque, l'inspection
dit avec quel code le processus est sorti. Les deux sources sont
complémentaires, et c'est la méthode du lab.

## 3. La politique de redémarrage de `appli-sans-fin`

À la ligne `politique=`.

Écrivez-la telle que **le moteur la déclare**, c'est-à-dire la valeur du nom de
la politique dans son inspection.

Elle ne se devine pas : **deux politiques différentes produisent exactement la
même boucle sans fin**, et elles ne se distinguent que sur un point qui n'a rien
à voir avec elle. Lisez-la **avant** de réparer : la retirer la ferait
disparaître.

## 4. Réparez, sans faire taire la boucle

```text
appli-sans-fin   doit TOURNER, avoir produit sa trace, et GARDER sa politique
appli-saine      doit être INTACTE, le conteneur du départ
```

Levez la cause, et **rendez la main au moteur**. Il rattrape de lui-même, en une
soixantaine de secondes : il attend entre deux tentatives, et ce délai croît.
Relancer le conteneur ne fait que ne pas attendre.

Retirer la politique serait le geste spontané, et c'est le mauvais : la boucle
cesserait parce que le conteneur cesserait d'être relancé, et le défaut serait
intact. **Ce n'est pas la politique qui est en faute, c'est la cause.**

Repartir d'une table rase serait pire : cela emporterait `appli-saine`, qui
tournait, et rien ne disait qu'elle était inutile. Le contrôle la reconnaît par
son identifiant, pas par son nom.

## Ce qui n'est pas noté

La commande que vous avez tapée. Le fichier manquant se dépose par n'importe
quel moyen, la reprise se fait en laissant le moteur rattraper comme en lui
rendant la main, et les trois valeurs s'interrogent de plusieurs façons.
