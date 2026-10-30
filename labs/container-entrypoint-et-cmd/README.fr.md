# container-entrypoint-et-cmd : lequel vos arguments remplacent-ils ?

## Ce que ce lab éprouve

La différence entre `ENTRYPOINT` et `CMD`, qui ne se voit pas dans l'image mais
dans ce qui arrive quand on passe des arguments à `docker run`. Deux règles
suffisent à tout expliquer, et le lab fait **rencontrer leurs quatre
conséquences** au lieu de les énoncer.

## Pourquoi les journaux, et non l'inspection de l'image

On pourrait lire `.Config.Entrypoint` dans l'inspection d'une image. Cela
noterait ce que l'image **déclare**, c'est-à-dire ce que le setup a écrit
lui-même : l'apprenant vérifierait le travail du lab, pas le sien.

Ce qui s'apprend ici est ce qui s'**exécute**, et le seul endroit où cela se lit
est la sortie du processus principal. D'où quatre conteneurs qui doivent
**rester**, et un énoncé qui le dit, parce qu'un `--rm` efface la preuve.

## Chaque contrôle vérifie aussi une absence

C'est ce qui le rend discriminant, et deux des quatre en dépendent entièrement :

| Conteneur | Présence attendue | Absence exigée |
| --- | --- | --- |
| `defaut` | `defaut-de-limage` | *aucune* |
| `remplace` | `remplacement-total` | `defaut-de-limage` |
| `complete` | le préfixe **et** `complement-cmd` | *aucune* |
| `contourne` | `sans-prefixe` | le préfixe |

Sans la partie « et pas ceci », un conteneur qui afficherait le défaut **et**
le texte demandé passerait le contrôle 2 alors qu'il n'a rien remplacé. Le
message de refus nomme d'ailleurs cette faute, parce qu'elle est le symptôme
d'une règle mal comprise et non d'une faute de frappe.

## L'état de départ est cassé, et c'est la règle du dépôt

Le setup pose les deux images et **aucun conteneur**. Les quatre contrôles sont
donc faux au départ, et une tâche le vérifie avant de rendre la main : les deux
images présentes, aucun des quatre noms pris. Un setup qui poserait un
conteneur ferait la démonstration à la place de l'apprenant.

## Pourquoi des images construites ici plutôt que tirées

Les deux comportements à comparer dépendent de deux lignes d'un Dockerfile.
Aucune image publique ne les porte dans la forme exacte dont ce lab a besoin, et
en tirer deux rendrait la démonstration opaque : l'apprenant doit pouvoir
**lire** les deux déclarations, qui sont déposées à côté dans
`/opt/lab-entrypoint`.

Les deux `FROM` portent le marqueur `dsoxlab:tag-nu-volontaire`. Ils reprennent
pourtant bien le digest : le marqueur est là parce que le détecteur
d'épinglage lit le Dockerfile généré sans savoir que la variable Ansible qu'il
y voit **est** un digest.

## Ce que le lab n'exige pas

Une forme. Deux des quatre résultats s'obtiennent aussi bien en forme exec
qu'en forme shell, et les deux comptent : le lab note un comportement, pas un
style d'écriture.
