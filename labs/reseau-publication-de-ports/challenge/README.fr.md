# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Trois conteneurs
**tournent déjà**, tous bâtis sur l'image `lab-publication:1.0`, qui écoute sur
son port 80 et répond un jeton.

Les trois sont mal publiés, chacun à sa façon. L'adresse routable de la machine
est donnée dans `/opt/MISSION.md`, et vous pouvez aussi la lire avec
`ip -4 addr`.

## 1. `vitrine` : sur le loopback seulement

Elle est publiée sur **toutes** les interfaces. Elle ne doit l'être que sur
`127.0.0.1`, port **18080** de l'hôte.

`-p 18080:80` ne publie pas « sur la machine » : l'adresse de publication est
**optionnelle**, et son défaut est le plus ouvert des trois. Nommez-la.

Le contrôle vérifie deux choses : ce que le moteur déclare, et que le service
répond encore en loopback. Publier n'est pas servir.

## 2. `vitrine` n'est plus joignable depuis le réseau

C'est la conséquence observable, et la seule qui compte vraiment.

Le contrôle précédent lit ce que le moteur **déclare** ; celui-ci éprouve ce que
la machine **fait**. Les deux peuvent diverger.

## 3. `annexe` : sur la seule adresse routable

Elle ne publie **rien**. Elle doit être publiée sur l'adresse routable de la
machine, port **18081**, et là seulement.

C'est le cas réel qu'on oublie : un service qu'on veut joindre depuis le réseau,
mais pas depuis tout ce qui tourne sur la machine.

Le contrôle le vérifie dans les **deux** sens : joignable par l'adresse
routable, et **pas** par `127.0.0.1`. Une publication sur toutes les interfaces
satisferait le premier sens seul.

## 4. `interne` : aucun port publié, et toujours joignable

Elle est publiée sur le port 18082 de l'hôte. Elle ne doit publier **aucun**
port, tout en restant joignable par les autres conteneurs.

C'est la posture qu'on oublie. Un service que seuls les autres conteneurs
doivent joindre n'a aucune raison d'être publié : ils l'atteignent par le
réseau, sans port sur l'hôte.

Les deux exigences sont indissociables, et c'est pourquoi elles ne font qu'un
contrôle : ne rien publier serait trivial en détruisant le conteneur.

## Ce qu'il faut savoir avant de commencer

**La publication ne se modifie pas à chaud.** Aucune commande ne change le `-p`
d'un conteneur existant : il faut le détruire et le recréer, sous le **même
nom**.

L'image porte son écouteur, donc relancer un conteneur ne demande aucune
commande particulière :

```bash
docker run -d --name <nom> <options de publication> lab-publication:1.0
```

Le jeton change à chaque recréation, et c'est normal.

## Un conseil d'outillage

Ne vous contentez pas d'une connexion qui aboutit. Le proxy de Docker accepte
avant que quoi que ce soit n'écoute : **lisez la réponse**. `nc -w 3 <adresse>
<port>` doit afficher une ligne `jeton=...`.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les conteneurs se recréent en ligne de commande
comme par l'API. Seul l'état compte.
