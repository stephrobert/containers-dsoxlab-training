# troubleshoot-boucle-de-redemarrage : la politique ne répare rien

## Ce que ce lab éprouve

Qu'une politique de redémarrage ne corrige aucun défaut. Elle décide seulement
de ce qui se passe **après** l'échec, et trois conteneurs qui partagent le même
défaut s'en sortent de trois façons :

| Politique | Ce qu'elle donne | Ce qu'on en conclut |
| --- | --- | --- |
| plafonnée | le moteur relance N fois, puis renonce | l'échec est figé, donc lisible |
| sans fin | il relance indéfiniment | l'échec est bruyant, et toujours là |
| sans fin, cause levée | il rattrape tout seul | il suffisait de lever la cause |

Le geste spontané est de faire cesser le bruit : retirer la politique, ou
détruire le conteneur. Les deux marchent, et les deux ne règlent rien.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Politique | État | RestartCount | Code de sortie |
| --- | --- | --- | --- |
| `on-failure:4` | `exited` | figé à **4** | celui du script |
| `always` | `restarting` | **10 en 60 s** | celui du script |
| `always`, cause levée | `running` | figé | sans objet |

Et le fait qui porte la seconde moitié du lab : **le conteneur en politique
infinie est reparti tout seul**, mesuré à une soixantaine de secondes après le
dépôt du fichier manquant, sans qu'on le touche. Le moteur attend entre deux
tentatives, et ce délai croît. Relancer le conteneur ne fait que ne pas
attendre.

Le conteneur plafonné, lui, n'est pas reparti : le moteur avait renoncé.

## Pourquoi le conteneur plafonné est le témoin

Il porte **deux** des trois réponses, et ses deux valeurs sont stables
précisément parce que le moteur a renoncé : le compteur ne bouge plus, et le
code reste celui de la dernière tentative.

L'énoncé interdit de le réparer, et un contrôle vérifie qu'il est resté
`exited`. Un conteneur relancé repart de zéro, sans compteur de relances ni
code de sortie : la question n'aurait plus d'objet. C'est la règle que la
section a dégagée, et c'est sa quatrième application : **une valeur de
diagnostic ne se lit jamais sur l'objet que la réparation modifie.**

## Pourquoi deux politiques, et tirées au hasard

`always` et `unless-stopped` produisent **exactement la même boucle**. Elles ne
se distinguent que sur un point qui n'a rien à voir avec elle, et c'est le sort
d'un conteneur arrêté à la main quand le moteur redémarre.

Le setup en tire une au hasard à chaque passage. La question ne se devine donc
pas, elle se lit, et elle se lit **avant** de réparer : retirer la politique la
ferait disparaître.

Le plafond et le code d'échec sont tirés de la même façon. Le code évite 0, 1,
2 et la plage 125-127, qui ont chacun un sens dans ce catalogue et
orienteraient le diagnostic par élimination.

## Pourquoi le quatrième contrôle exige la politique intacte

Retirer la politique fait cesser la boucle **sans rien régler** : le conteneur
cesse d'être relancé, et le défaut est entier. C'est la faute que ce lab existe
pour empêcher, et un contrôle qui ne regarderait que « le conteneur ne boucle
plus » la récompenserait.

Il exige donc trois choses d'un coup : le conteneur tourne avec la trace de son
script, sa politique est toujours celle du départ, et le conteneur sain est
**celui du départ**, reconnu par son identifiant et non par son nom. Un
homonyme recréé après une table rase porterait le même nom, et c'est justement
le geste qui emporte un service qui tournait.

## Pourquoi le contrôle accorde du temps, mais pas toujours

Le délai du moteur atteint la minute. Un apprenant qui lève la cause et note
aussitôt serait refusé pour avoir fait exactement ce qu'il fallait, et il en
retiendrait qu'il faut recréer.

Le contrôle attend donc jusqu'à 150 secondes, **mais seulement quand la cause
est levée** : il vérifie d'abord la présence du fichier qui manquait, et refuse
sans attendre quand il est toujours absent. Un `check` joué sans rien avoir
corrigé répond tout de suite.

## Pourquoi le setup constate la boucle sur le compteur

Mesuré le 2026-10-30 : entre deux tentatives, le conteneur en boucle passe par
`running` le temps que son script échoue. Un contrôle sur l'état est donc vrai
une fois sur deux, et le premier jet du setup a échoué là.

Le compteur de relances, lui, ne redescend jamais. C'est la preuve stable qu'un
conteneur boucle.

## Un piège du cleanup, payé d'avance

Les conteneurs partent **avant** leur configuration. Deux d'entre eux portent
une politique de redémarrage, et le moteur les relance tant qu'ils existent :
retirer le répertoire d'abord laisserait l'un d'eux boucler sur une
configuration disparue, en remplissant le journal du moteur.

## Ce que le lab n'exige pas

Un chemin. Le fichier manquant se dépose par n'importe quel moyen, et la
reprise se fait en laissant le moteur rattraper comme en lui rendant la main.
Les trois valeurs se lisent dans l'inspection, qui s'interroge de plusieurs
façons.
