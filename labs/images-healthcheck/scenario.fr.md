# Un conteneur « up » qui ne travaille plus

## La situation

Le tableau de bord est vert. Le conteneur est « up » depuis trois jours, son
processus tourne, sa consommation est normale.

Et le service ne traite plus rien depuis deux heures.

Personne ne le sait, parce que rien ne regardait le **travail** : la
supervision regardait le processus, et le processus n'est jamais mort.

## L'objectif

Le contexte est dans `/opt/lab-sante/appli`. Le service y bat un **pouls** : il
écrit l'heure dans `/var/run/pouls` chaque seconde, tant qu'il travaille.

Construisez le Dockerfile tel quel sous le nom `appli:surveillee`, lancez-le
sous le nom `service-surveille`, et inspectez-le. Il n'a **aucun** état de
santé : le champ n'existe pas.

Rendez maintenant le service muet, sans tuer son processus :

```bash
docker exec service-surveille touch /tmp/muet
```

Le conteneur est toujours « up ». Son pouls est rance. Personne ne le sait.

Ajoutez une sonde, reconstruisez, relancez. `service-surveille` doit :

```text
atteindre l'état SAIN quand le service travaille
passer MALADE quand le pouls devient rance, le processus vivant
REVENIR à SAIN quand le service repart
déclarer des bornes cohérentes
```

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce qui est mesuré, et qui décide du lab

| Situation | Ce que le moteur déclare |
| --- | --- |
| aucune sonde | **aucun** état de santé, le champ n'existe pas |
| sonde sur la fraîcheur du pouls, service sain | `healthy` en 2 s |
| le même, service muet et processus vivant | `unhealthy` en 8 s |
| le même, service rétabli | retour à `healthy` en 2 s |
| sonde sur le **processus**, service muet | **`healthy`**, pouls rance |

La dernière ligne est le lab. Une sonde qui regarde le processus ne voit rien,
et c'est mesuré : elle déclare le service sain pendant que son pouls vieillit.

## Une surprise que ce lab ne note pas

**Un conteneur `unhealthy` reste en marche.** Le moteur ne l'arrête pas, ne le
relance pas et ne prévient personne. Une sonde **informe** ; elle ne répare
rien, et elle ne décide de rien sans un orchestrateur pour la lire.

Aucun contrôle n'attend donc un arrêt : ce serait mesurer une croyance.

## Les bornes ne sont pas des détails

Le quatrième contrôle exige deux choses, chacune pour une raison :

- **au moins deux tentatives**, sans quoi un hoquet d'une seconde déclare
  malade un service qui va bien ;
- une **période de démarrage**, sans quoi un service qui prend du temps à se
  préparer est jugé avant d'avoir commencé.

Le **délai d'attente** n'est pas contrôlé, et c'est mesuré : l'intervalle se
compte après la **fin** d'une sonde, jamais entre deux départs. Une sonde qui
dure six secondes sous un intervalle de deux secondes ne produit donc aucun
empilement. Relevé sur Docker Engine 29.1.3 : une seule sonde en vol à tout
instant, et deux secondes pile entre la fin d'une sonde et le départ de la
suivante. Le délai d'attente sert à autre chose : il borne une sonde qui ne rend
pas la main, et se choisit juste au-dessus de la durée normale de la sonde.

## Ce qui est noté

L'**état du système**, et les délais accordés sont **calculés** : chaque
contrôle lit les bornes que votre image déclare et en dérive le temps qu'il
attend. Une valeur en dur refuserait une sonde prudente, ou accepterait une
sonde qui ne conclut jamais.

Le troisième contrôle est celui qu'on n'attend pas : il remet le service en
marche et exige le retour au sain. Une sonde qui garde la trace de son premier
échec passerait les deux autres, et ne servirait qu'une fois.
