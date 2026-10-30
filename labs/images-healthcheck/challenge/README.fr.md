# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le contexte est dans
`/opt/lab-sante/appli` :

```text
Dockerfile   il MARCHE, et ne déclare AUCUNE sonde
servir.sh    le service, qui bat un pouls dans /var/run/pouls chaque seconde
```

Construisez sous le nom `appli:surveillee`, lancez sous le nom
`service-surveille`, et inspectez : il n'y a pas de champ de santé.

Puis rendez le service muet sans tuer son processus, avec
`docker exec service-surveille touch /tmp/muet`, et regardez ce que le moteur
dit du conteneur. Rien.

## 1. Le conteneur doit atteindre l'état sain

L'image doit déclarer une sonde, et le conteneur devenir **sain** quand le
service travaille.

Un conteneur sans sonde n'a pas un état « inconnu » : il n'a **aucun** champ de
santé. Confondre les deux fait chercher une sonde qui marche mal là où il n'y en
a aucune.

## 2. Il doit passer malade quand le pouls devient rance

C'est le cœur du lab.

Le service se tait, et **son processus continue de tourner**. Mesuré : une sonde
qui regarde le processus déclare le service sain pendant que son pouls
vieillit. Ce qu'il faut sonder, c'est le **travail**, et le pouls en est la
preuve : sa **fraîcheur**, pas son existence.

Le fichier de pouls existe toujours, même muet. Seul son horodatage vieillit.

## 3. Il doit revenir sain quand le service repart

Une sonde dit l'état **courant**, et non ce qu'elle a vu une fois.

Sans ce contrôle, une sonde qui garde la trace de son premier échec, dans un
fichier ou un drapeau, passerait les deux précédents : elle conclurait au sain,
puis au malade, et y resterait pour toujours.

## 4. Les bornes déclarées doivent être cohérentes

```text
délai d'attente < intervalle    sinon les sondes s'empilent
au moins 2 tentatives           sinon un hoquet déclare malade
une période de démarrage        sinon un service lent est jugé avant de commencer
```

## Une surprise, et ce que le lab n'en fait pas

**Un conteneur malade reste en marche.** Le moteur ne l'arrête pas, ne le
relance pas, ne prévient personne : une sonde informe, elle ne répare rien.

Aucun contrôle n'attend donc un arrêt. Ce serait mesurer une croyance.

## Ce qui n'est pas noté

La forme de la sonde, ni ses valeurs exactes. Les délais accordés sont
**calculés** depuis les bornes que votre image déclare : une sonde prudente
n'est pas pénalisée, et une sonde qui ne conclut jamais n'est pas acceptée.
