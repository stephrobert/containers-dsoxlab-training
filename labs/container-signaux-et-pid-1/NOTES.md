# container-signaux-et-pid-1 : qui est PID 1 décide de tout

## Ce que ce lab éprouve

Qu'un conteneur qui met le délai complet à s'arrêter est un conteneur qu'on
**tue**, et que la cause est presque toujours la même : le processus qui reçoit
le signal n'est pas celui qui saurait l'entendre.

## Ce qui a été mesuré avant d'écrire ce lab, et qui a changé sa conception

L'explication courante dit « forme shell, donc le shell est PID 1 ». **Elle est
fausse sur cette image.** Mesuré le 2026-10-29 sur Alpine :

| Forme | PID 1 | Code | Arrêt |
| --- | --- | --- | --- |
| `ENTRYPOINT ["/app.sh"]` | `app.sh` | 0 | 1 s |
| `ENTRYPOINT /app.sh` | **`app.sh`** | **0** | **1 s** |
| `ENTRYPOINT /app.sh ; echo x` | `sh` | 137 | 6 s |

Busybox optimise la commande unique en un `exec` direct : la forme shell seule
ne produit donc **aucun** piège. Un lab bâti sur l'explication courante aurait
comparé deux images au comportement identique, et deux de ses quatre contrôles
auraient été indistinguables. Il serait passé au vert en n'enseignant rien.

Ce qui produit vraiment le défaut est le cas réel le plus fréquent : un script
d'entrée qui lance l'application en **enfant**.

| Script d'entrée | PID 1 | Code | Arrêt | Journaux |
| --- | --- | --- | --- | --- |
| `/app.sh` | `entree.sh` | 137 | 6 s | pas de SIGTERM |
| `exec /app.sh` | `app.sh` | 0 | 1 s | SIGTERM reçu |

Un seul mot les sépare, et trois conséquences le montrent. C'est aussi la
correction qu'on écrit dans la vraie vie.

## Le premier contrôle exige le symptôme, pas sa correction

`fragile` doit avoir été arrêté et porter un code non nul, et ses journaux ne
doivent **pas** porter la trace du signal. C'est délibéré : un apprenant doit
avoir **vu** le défaut avant de le corriger, sinon il corrige une consigne et
non un problème.

Le message de refus prévoit même le cas où il aurait « réparé » ce conteneur :
il lui dit de rejouer le lab, parce que la pièce à conviction est perdue.

## Le piège de la fausse correction, et comment il est fermé

Vider le script d'entrée corrigerait le signal. Ce serait aussi supprimer la
raison d'être du script, et un apprenant pourrait le faire sans jamais
rencontrer `exec`.

Le quatrième contrôle exige donc que `preparation-faite` figure encore dans les
journaux. Un contrôle qui n'interdit pas la mauvaise solution finit par la
récompenser.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `fragile` | `running`, PID 1 = `entree.sh` | l'arrêter et constater | 1 |
| *rien* | pas d'`img-corrige:1.0` | la construire | 2 |
| *rien* | pas de `robuste` | le lancer puis l'arrêter | 3 et 4 |

Une tâche du setup **vérifie** cet état avant de rendre la main, y compris le
PID 1 du conteneur fautif : si l'optimisation du shell changeait un jour, le
lab le dirait au lieu de noter n'importe quoi.

## Un détail du deuxième contrôle

Il lance un conteneur jetable pour lire le PID 1, et ce conteneur porte le
préfixe `dsoxlab-` du dépôt, posé par `nom_objet()`, puis est retiré en
`finally`. C'est la discipline du `conftest.py` : la machine porte des
centaines d'objets, et un conteneur oublié par un test s'y noierait.

## Ce que le lab n'exige pas

Une façon de corriger. `exec` dans le script d'entrée, l'application invoquée
directement par l'`ENTRYPOINT`, ou un init qui réexpédie les signaux aboutissent
tous à un PID 1 qui entend SIGTERM. Le contrôle lit le nom du processus, pas le
Dockerfile.
