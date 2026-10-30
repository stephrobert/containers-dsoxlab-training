# internes-chaine-dexecution : qui lance vraiment un conteneur

## Ce que ce lab éprouve

Que le processus d'un conteneur n'est l'enfant d'aucun des programmes qu'on
croit. La chaîne, mesurée sur `docker.lab` le 2026-10-30 :

```text
sleep (le processus du conteneur)
  ← containerd-shim-runc-v2  (un par conteneur)
    ← PID 1                  (le gestionnaire de services, PAS le démon)
```

Le démon et le service de conteneurs sont deux services distincts, de PID
distincts, et **aucun des deux n'est le parent du shim**.

C'est le dernier lab des internes : après ce qu'un conteneur voit, ce qu'il peut
consommer et où ses fichiers atterrissent, qui le lance.

## Une idée reçue que la mesure a démentie, et elle a changé le lab

**La première version de ce lab faisait redémarrer le démon** pour constater que
les conteneurs y survivent. Le raisonnement semblait solide : le shim n'est pas
enfant du démon, donc le démon peut tomber sans l'emporter.

Mesuré le 2026-10-30, et la validation l'a attrapé en rendant le lab ROUGE : le
PID du conteneur **avait changé**.

| Moment | PID du conteneur | PID du démon |
| --- | --- | --- |
| avant le redémarrage | 214470 | 214266 |
| après | **214951** | 214729 |

Sans le réglage `live-restore`, qui n'est pas le défaut, le démon arrête ses
conteneurs en partant et les relance. Le détachement du shim rend la survie
**possible**, il ne la **produit** pas.

**Un lab ne peut pas faire constater une chose fausse.** Le quatrième contrôle a
donc changé de geste : un second conteneur, et chacun a son propre shim, tous
détachés du même parent. C'est la même propriété de la chaîne, démontrée
autrement.

## Et une raison de plus de ne pas toucher au démon

En éprouvant l'hypothèse, les redémarrages répétés ont déclenché la limite de
systemd (« start of the service was attempted too often »), et le démon a
refusé de repartir jusqu'à un `reset-failed`.

Un lab qui redémarre un service **trois fois par cycle de validation** se serait
cassé de la même façon, et il aurait échoué pour une raison étrangère à son
sujet. Le geste actuel ne touche à aucun service.

## Pourquoi le shim est trouvé par l'identifiant du conteneur

La machine en porte autant que de conteneurs. Un `pgrep` sur le nom du programme
rendrait le premier venu, ce qui marcherait tant qu'un seul conteneur tourne et
mentirait dès le second, c'est-à-dire exactement au moment où le quatrième
contrôle commence.

Les contrôles cherchent donc la ligne de commande qui **cite l'identifiant** du
conteneur visé.

## Aucun PID n'est écrit, pas même le 1

Le parent du shim est **lu**, et non attendu. Sur une machine réglée autrement,
le détachement pourrait aboutir ailleurs, et ce lab suivrait au lieu de devenir
faux.

La solution de référence applique la même règle, et c'est ce qui en fait une
démonstration de méthode plutôt qu'une récitation.

## Le runtime est lu dans la bonne source

Deux sources l'indiquent : le défaut du moteur, et celui du conteneur. Les deux
coïncident sur cette machine, et ne coïncideraient pas sur une machine qui en
installe plusieurs.

Le contrôle accepte celui du **conteneur**, qui est le seul vrai pour ce
conteneur.

## Le quatrième contrôle demande trois faits à la fois

Le second conteneur existe, son shim est **différent** du premier, et les deux
ont le **même** parent.

Les trois ne se séparent pas : sans le troisième, deux shims distincts
pourraient venir de deux chaînes différentes, et la démonstration serait
incomplète.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | trois clés, trois valeurs **vides** | les renseigner | 1, 2 et 3 |
| `maillon` | tourne, avec son marqueur | ne pas y toucher | tous |
| *rien* | `maillon-bis` absent | le lancer | 4 |

## Un geste du cleanup qui n'est pas décoratif

Il s'assure que le moteur est **debout** à la fin. L'apprenant a pu arrêter le
démon au lieu de simplement regarder, et le lab suivant partirait alors d'une
machine sans moteur, en accusant son propre setup.

## Ce que le lab n'exige pas

Un chemin. Le shim se trouve par la liste des processus comme par l'arbre des
processus, le parent par plusieurs outils, et le runtime se lit dans deux
sources. Seul l'état compte.
