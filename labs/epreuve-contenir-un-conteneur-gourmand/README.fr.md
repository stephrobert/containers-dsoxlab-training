# epreuve-contenir-un-conteneur-gourmand : l'épreuve du module sur le moteur

## Ce que cette épreuve éprouve

Contenir un conteneur par ses cgroups, et prouver que la contention tient. Elle
clôt le module « Comprendre ce que fait le moteur » et ne réexplique rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## Le piège, et il est entier

Poser des limites exige de **recréer** le conteneur : un cgroup se pose à la
création, et les changer sur un conteneur en cours ne les applique pas. Or le
conteneur monte un volume qui porte des résultats irremplaçables.

**C'est donc une épreuve de prudence autant que de technique.** Qui recrée vite
perd les données, et le contrôle ne lui pardonne pas : il compare des empreintes,
pas des noms, et un volume recréé vide puis regarni par le traitement ne le
trompe pas.

## Pourquoi la pointe est bornée, et ce que cela a coûté de décider

La pointe alloue par doublement jusqu'à dépasser une cible, puis rend la main :
mesuré sur cette machine le 2026-11-02, cela plafonne à 256 Mo et l'hôte garde
1,4 Go libre.

Le premier dessin utilisait `tail /dev/zero`, qui alloue **sans fin**. Sur une VM
de 2 Go, le passage « avant travail » du cycle de validation, où aucune limite
n'existe encore, aurait fait tuer `sshd` ou le démon par l'OOM de l'hôte. Une
épreuve ne doit pas pouvoir emporter la machine qui la mesure, et un validateur
qui perd sa cible ne rend aucun verdict.

## Ce que la mesure a établi, et qui fonde le contrôle de la pointe

| Situation | Résultat mesuré |
| --- | --- |
| sans limite | l'allocation réussit, 536 870 912 octets, l'hôte tient |
| avec 128 Mo | le cgroup tue l'**enfant** gourmand (`oom_kill 1`), le PID 1 survit, le conteneur reste `running` |

Le contrôle lit donc `memory.peak` et `memory.events`. Et il exige que la limite
ait été **atteinte** : sans cela, un apprenant qui poserait une limite énorme
passerait le contrôle sans que la pointe ait rien éprouvé.

## Pourquoi « le traitement répond encore » est un contrôle séparé

Parce que sa cause est différente. **Contenir n'est pas tuer** : une limite bien
posée tue le processus gourmand, pas le service. Un apprenant qui poserait 8 Mo
de limite contiendrait parfaitement la pointe, et son application serait morte.
Fusionner les deux contrôles rendrait ce cas indiscernable d'une réussite.

## Pourquoi le cgroup est lu depuis le conteneur

Le chemin du scope sur l'hôte dépend du pilote de cgroup et de la version de
systemd, alors que `/sys/fs/cgroup` est monté dans le conteneur sur son propre
cgroup. C'est plus simple et plus portable. Et, mesuré dans ce catalogue, ces
fichiers se lisent **sans privilège** : les écrire en demande un, et c'est ce qui
sépare l'observation du réglage.

## Ce que l'épreuve ne mesure pas

Le réseau, les secrets, le durcissement. Ce sont les sujets d'autres épreuves.
