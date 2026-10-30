# Un conteneur qui boucle, un autre que le moteur a abandonné

## La situation

L'alerte dit « conteneur en boucle de redémarrage », et c'est tout. On regarde,
et effectivement : la liste des conteneurs montre l'un d'eux qui repart, échoue,
repart encore. Le journal du moteur se remplit.

Le geste spontané est de faire cesser le bruit : retirer la politique de
redémarrage, ou détruire le conteneur. Les deux marchent, et les deux ne règlent
rien. **Ce n'est pas la politique qui est en faute.** Elle ne fait que rendre
l'échec visible, en le répétant. Le conteneur échouait déjà au premier essai.

Et à côté, un deuxième conteneur a le même défaut sans boucler du tout : le
moteur a renoncé à le relancer. Deux comportements, un seul défaut, et c'est la
politique qui explique l'écart.

## L'objectif

Trois conteneurs, un seul défaut :

```text
appli-plafond    le moteur a RENONCÉ à le relancer
appli-sans-fin   le moteur le relance encore, et encore
appli-saine      tourne, et doit continuer de tourner
```

Lisez d'abord les traces de `appli-sans-fin`. Elles disent ce qui manque, et
elles le disent autant de fois qu'il y a eu de tentatives : c'est ce qui rend un
journal de conteneur en boucle si pénible à lire, et c'est aussi la preuve que
toutes les tentatives échouent de la même façon.

Renseignez les trois lignes de `/opt/lab-boucle/reponses.txt` :

```text
tentatives=<combien de fois le moteur a relancé appli-plafond>
code=<le code de sortie de appli-plafond>
politique=<la politique de redémarrage de appli-sans-fin, telle que le moteur
           la déclare>
```

**Ne réparez pas `appli-plafond`** : c'est sur lui que se lisent les deux
premières réponses, et un conteneur relancé repart de zéro, sans compteur ni
code de sortie.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Deux politiques donnent la même boucle

La troisième question ne se devine pas. Deux politiques différentes produisent
exactement la même boucle sans fin, et elles ne se distinguent que sur un point
qui n'a rien à voir avec elle. Il faut donc la lire, et la lire **avant** de
réparer : réparer en retirant la politique la ferait disparaître.

## La réparation, et c'est là que le lab a un avis

`appli-sans-fin` doit **tourner**, avoir produit sa trace, et **garder sa
politique**. Et `appli-saine` doit être intacte, le conteneur du départ.

Levez la cause, et **rendez la main au moteur** : il rattrape de lui-même, en
une soixantaine de secondes, parce qu'il attend entre deux tentatives et que ce
délai croît. Relancer le conteneur ne fait que ne pas attendre.

Retirer la politique serait le geste spontané, et c'est le mauvais : la boucle
cesserait parce que le conteneur cesserait d'être relancé, et le défaut serait
intact. Repartir d'une table rase serait pire encore : cela emporterait un
service qui tournait, et rien ne disait qu'il était inutile.

## Ce qui est noté

L'**état du système**. Le plafond, le code et la politique sont **tirés au
hasard à chaque passage** : rien dans le dépôt ne les porte, et les contrôles
les recalculent en interrogeant le moteur au moment de la notation.

Le quatrième contrôle vérifie les trois moitiés de la réparation : que le
conteneur tourne, que sa politique est toujours là, et que le conteneur sain est
bien celui du départ, reconnu par son identifiant et non par son nom.
