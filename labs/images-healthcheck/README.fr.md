# images-healthcheck : « up » ne dit rien du service

## Ce que ce lab éprouve

Qu'un conteneur en marche ne dit rien du travail, et qu'une sonde qui regarde le
**processus** n'en dit pas davantage. La panne la plus fréquente n'est pas le
processus qui meurt : c'est le service qui se tait sans mourir.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Situation | Ce que le moteur déclare |
| --- | --- |
| aucune sonde | **aucun** état de santé, le champ n'existe pas |
| sonde sur la fraîcheur du pouls, service sain | `healthy` en 2 s |
| le même, service muet et processus vivant | `unhealthy` en 8 s |
| le même, service rétabli | retour à `healthy` en 2 s |
| sonde sur le **processus**, service muet | **`healthy`**, pouls rance |

La dernière ligne est le lab, et elle est mesurée, pas déduite.

## Pourquoi un pouls, et non un port

Le premier jet servait sur un port avec `nc`, et la sonde n'atteignait **jamais**
l'état sain. La cause n'avait rien à voir avec le sujet : un `nc -l` de busybox
ne sert qu'une connexion, et la synchronisation entre la sonde et la boucle
décidait du verdict.

Un pouls ne dépend d'aucun réseau, d'aucun client, d'aucun temps de connexion.
Il garde la seule propriété qui compte : le service peut cesser de travailler
sans que son processus meure.

## Pourquoi aucun contrôle ne porte sur les ports ni sur un arrêt

**Un conteneur `unhealthy` reste en marche**, mesuré : le moteur ne l'arrête
pas, ne le relance pas, ne prévient personne. Une sonde informe ; elle ne répare
rien sans un orchestrateur pour la lire.

Un contrôle qui attendrait un arrêt mesurerait une croyance répandue, et un lab
qui note une croyance l'enseigne. C'est la même décision que dans
`images-non-root`, où la mesure a montré qu'un non-root écoute sous 1024 et où
aucun contrôle ne porte donc sur les ports.

## Pourquoi les délais sont calculés et non écrits

Chaque contrôle lit les bornes que l'image déclare, et en dérive le temps qu'il
accorde : période de démarrage, puis autant d'intervalles que de tentatives,
chacun pouvant aller jusqu'à son délai d'attente, plus un intervalle de marge.

Un délai en dur refuserait une sonde prudente, ou accepterait une sonde qui ne
conclut jamais. Un plancher reste posé, pour qu'une sonde très rapide ne soit
pas jugée sur un hasard de synchronisation.

## Pourquoi le troisième contrôle existe

Une sonde qui garde la trace de son premier échec, dans un fichier ou un
drapeau, passerait les deux premiers : sain, puis malade, et malade pour
toujours. Le troisième remet le service en marche et exige le retour au sain.

Une sonde dit l'état **courant**. Celle qui ne sait dire qu'une fois ne surveille
rien.

## Un défaut de lecture, attrapé par le cycle

Le test et la solution supposaient des bornes en nanosecondes entières. Mesuré :
le moteur rend une **durée formatée**, `5s`, et `1m30s` pour quatre-vingt-dix
secondes.

Côté shell, `test -lt` répondait « Illegal number: 2s ». Côté Python, `int("2s")`
levait, la fonction rendait un dictionnaire vide, et le premier contrôle
annonçait **« aucune sonde déclarée » sur une image qui en portait une**. Le
message accusait l'inverse de ce qui était vrai.

Les bornes se lisent désormais par `.Seconds`, que Go expose sur une durée : il
n'y a pas de `1m30s` à parser, donc pas de parseur à se tromper.

## L'état de départ est cassé, et c'est la règle du dépôt

Ni l'image ni le conteneur n'existent : les quatre contrôles sont faux avant tout
travail. Une tâche du setup vérifie que le socle existe, que l'image de
l'apprenant n'existe pas, et que le Dockerfile de départ ne porte **aucune**
sonde.

## Ce que le lab n'exige pas

Une forme de sonde, ni des valeurs précises. Le jeton est tiré par le setup, les
bornes sont celles de l'image, et les délais en découlent : rien n'est écrit en
dur dans les contrôles.
