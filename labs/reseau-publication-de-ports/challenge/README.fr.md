# La base de données répondait depuis Internet

## La situation

Un audit passe sur votre serveur et remonte une ligne qui vous glace : la base
de données d'une application interne répond depuis l'extérieur. Personne ne l'a
ouverte. Il n'y a aucune règle de pare-feu qui l'autorise, et vous êtes
certain de n'avoir jamais rien exposé.

Vous relisez la commande qui a lancé le conteneur. Elle dit :

```text
docker run -d --name base -p 5432:5432 postgres
```

Le `-p 5432:5432` ne publie pas « sur la machine ». Il publie sur **toutes les
interfaces**, parce que l'adresse de publication est **optionnelle** et que son
défaut est le plus ouvert des trois possibles. Le port était ouvert depuis le
premier jour, et il n'a jamais figuré dans aucune décision.

## L'objectif

Corriger trois conteneurs mal publiés, un par posture. Les trois sont bâtis sur
l'image `lab-publication:1.0`, qui écoute sur son port 80 et répond un jeton.

```text
vitrine   publiée sur TOUTES les interfaces
          → ne doit l'être QUE sur 127.0.0.1, port 18080 de l'hôte

annexe    ne publie RIEN
          → doit l'être uniquement sur l'adresse ROUTABLE, port 18081

interne   publiée sur le port 18082 de l'hôte
          → ne doit publier AUCUN port, tout en restant joignable par les
            autres conteneurs
```

Gardez les noms : les contrôles les cherchent nommément. L'énoncé est aussi
déposé dans `/opt/MISSION.md`, avec l'adresse routable de la machine.

## Ce qu'il faut savoir avant de commencer

**La publication d'un conteneur ne se modifie pas à chaud.** Aucune commande ne
change le `-p` d'un conteneur existant : il faut le détruire et le recréer.

C'est pour cette raison que l'image porte son écouteur : relancer un conteneur
ne demande aucune commande particulière.

```bash
docker run -d --name <nom> <options de publication> lab-publication:1.0
```

Le jeton change à chaque recréation, et c'est normal : les contrôles lisent la
réponse du service, pas le jeton d'hier.

## Ce qui est noté

L'**état du système**, et il est mesuré deux fois pour chaque posture : ce que
le moteur **déclare** publier, et ce que la machine **fait** réellement.

Les deux peuvent diverger, et c'est pour cela que les deux sont mesurés. Un
détail qui compte ici : les contrôles lisent la **réponse** du service, jamais
la seule connexion. Le proxy de Docker accepte une connexion avant que quoi que
ce soit n'écoute, donc un port qui « répond » peut très bien ne mener nulle
part.

## La posture qu'on oublie

Ne rien publier. Un service que seuls les autres conteneurs doivent joindre n'a
aucune raison d'être publié : ils l'atteignent par le réseau, sans port sur
l'hôte.

Publier est le réflexe, et c'est ce réflexe qui expose les bases de données.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Trois conteneurs
**tournent déjà**, tous bâtis sur l'image `lab-publication:1.0`, qui écoute sur
son port 80 et répond un jeton.

Les trois sont mal publiés, chacun à sa façon. L'adresse routable de la machine
est donnée dans `/opt/MISSION.md`, et vous pouvez aussi la lire avec
`ip -4 addr`.

### 1. `vitrine` : sur le loopback seulement

Elle est publiée sur **toutes** les interfaces. Elle ne doit l'être que sur
`127.0.0.1`, port **18080** de l'hôte.

`-p 18080:80` ne publie pas « sur la machine » : l'adresse de publication est
**optionnelle**, et son défaut est le plus ouvert des trois. Nommez-la.

Le contrôle vérifie deux choses : ce que le moteur déclare, et que le service
répond encore en loopback. Publier n'est pas servir.

### 2. `vitrine` n'est plus joignable depuis le réseau

C'est la conséquence observable, et la seule qui compte vraiment.

Le contrôle précédent lit ce que le moteur **déclare** ; celui-ci éprouve ce que
la machine **fait**. Les deux peuvent diverger.

### 3. `annexe` : sur la seule adresse routable

Elle ne publie **rien**. Elle doit être publiée sur l'adresse routable de la
machine, port **18081**, et là seulement.

C'est le cas réel qu'on oublie : un service qu'on veut joindre depuis le réseau,
mais pas depuis tout ce qui tourne sur la machine.

Le contrôle le vérifie dans les **deux** sens : joignable par l'adresse
routable, et **pas** par `127.0.0.1`. Une publication sur toutes les interfaces
satisferait le premier sens seul.

### 4. `interne` : aucun port publié, et toujours joignable

Elle est publiée sur le port 18082 de l'hôte. Elle ne doit publier **aucun**
port, tout en restant joignable par les autres conteneurs.

C'est la posture qu'on oublie. Un service que seuls les autres conteneurs
doivent joindre n'a aucune raison d'être publié : ils l'atteignent par le
réseau, sans port sur l'hôte.

Les deux exigences sont indissociables, et c'est pourquoi elles ne font qu'un
contrôle : ne rien publier serait trivial en détruisant le conteneur.

### Ce qu'il faut savoir avant de commencer

**La publication ne se modifie pas à chaud.** Aucune commande ne change le `-p`
d'un conteneur existant : il faut le détruire et le recréer, sous le **même
nom**.

L'image porte son écouteur, donc relancer un conteneur ne demande aucune
commande particulière :

```bash
docker run -d --name <nom> <options de publication> lab-publication:1.0
```

Le jeton change à chaque recréation, et c'est normal.

### Un conseil d'outillage

Ne vous contentez pas d'une connexion qui aboutit. Le proxy de Docker accepte
avant que quoi que ce soit n'écoute : **lisez la réponse**. `nc -w 3 <adresse>
<port>` doit afficher une ligne `jeton=...`.

### Ce qui n'est pas noté

La commande que vous avez tapée. Les conteneurs se recréent en ligne de commande
comme par l'API. Seul l'état compte.
