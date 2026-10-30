# troubleshoot-exit-127 : une grille, pas un symptôme

## Ce que ce lab éprouve

Qu'un code de sortie est un **diagnostic**, et que deux codes voisins disent
deux choses opposées.

Un lab de dépannage ne s'enseigne pas avec un symptôme : il s'enseigne avec une
**grille**, et une grille demande des cas voisins qu'on puisse comparer. D'où
trois pannes plutôt qu'une.

C'est le premier des quatre labs de dépannage de la section.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Cause | Code | Journal | Statut |
| --- | --- | --- | --- |
| commande introuvable | 127 | **vide** | **`created`** |
| fichier non exécutable | 126 | vide | `exited` |
| commande qui échoue | son propre code | ce qu'elle a écrit | `exited` |

## La distinction qui vaut le lab entier

Quand la commande est introuvable, le conteneur **n'a jamais démarré**. Son
statut reste `created`, son journal est vide, et le diagnostic est dans
`.State.Error` de l'inspection, que personne ne regarde :

```text
unable to start container process: exec: "…": executable file not found in $PATH
```

En revanche, **si un shell enveloppe la commande, le journal parle**, parce que
le shell a démarré, lui. Mesuré : `sh: /tmp/inexistant: not found`.

Le même code 127, deux situations opposées, et le journal est ce qui les sépare.
C'est ce qui explique l'heure perdue du scénario : on cherche dans l'image une
cause que l'inspection annonçait en une ligne.

## Pourquoi trois pannes, et pourquoi le contrôle vérifie qu'elles diffèrent

Deux codes voisins ne s'apprennent que l'un par rapport à l'autre. Le deuxième
contrôle vérifie donc aussi que les deux codes **diffèrent** : une grille dont
deux cases portent la même valeur n'est pas une grille.

Le setup le vérifie également avant de poser le lab, ce qui le protège d'une
dérive future : si un changement d'image rendait deux pannes identiques, le lab
s'arrêterait au lieu d'enseigner une fausse distinction.

## La réparation se fait sur la même image, et c'est noté

Le conteneur réparé doit dériver de la **même image** que les pannes. C'est ce
qui démontre que l'image n'était pas en cause.

Réparer en changeant d'image prouverait l'inverse de la leçon, et le contrôle le
refuse explicitement. **Savoir ce qui n'est pas responsable écarte la moitié des
pistes** : c'est la conclusion la plus rentable d'un dépannage.

## Aucun code n'est écrit en dur

Les trois valeurs attendues sont lues sur les conteneurs au moment de la
notation. Un test qui aurait porté `127` serait faux le jour où le setup
changerait de panne, et le lab mourrait d'une modification sans rapport.

La solution de référence applique la même règle : elle **lit** les trois
réponses, et elle consulte en plus le champ d'erreur, qu'aucune question ne
demande. Son `failed_when` exige d'y trouver la trace attendue, donc elle le
**prouve** au lieu de le mentionner : une solution de référence est aussi un
document d'enseignement.

## Un détail du setup qui n'est pas une négligence

Les trois `docker run` du setup portent `failed_when: false`. C'est délibéré :
les trois commandes échouent, c'est tout l'objet du lab, et sans cette ligne le
setup s'arrêterait sur la première panne qu'il vient de poser.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | trois clés, trois valeurs **vides** | les renseigner | 1, 2 et 3 |
| trois pannes | arrêtées, trois codes distincts | les diagnostiquer | 1, 2 et 3 |
| *rien* | `repare` absent | le lancer sur la même image | 4 |

## Ce que le lab n'exige pas

Un chemin. Les codes se lisent dans l'inspection comme dans la liste des
conteneurs, et la réparation se fait avec n'importe quelle commande qui existe
et qui dure.
