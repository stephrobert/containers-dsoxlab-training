# Épreuve : remettre une stack en service

Reprenez le nom de projet et le chemin de fichier donnés par la mission.
L'image fournie existe déjà : l'épreuve porte sur **l'orchestration**, pas sur
la construction d'une image.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. Le projet porte ses deux services, et ils tournent

Exactement deux, `donnees` et `frontal`. Le nom du projet fait partie de
l'énoncé : c'est lui qui rattache conteneurs, réseaux et volumes les uns aux
autres, et sans lui Compose le dérive du nom du répertoire.

### 2. La requête métier joint les données par leur **nom de service**

La façade doit rendre la valeur que détient `donnees`. Le frontal interroge le
nom que `CIBLE` lui donne : ce nom est celui d'un **service**, et il ne se
contourne pas en renommant un conteneur. Si la façade rend
`amont-injoignable`, c'est que la jonction n'a pas lieu.

### 3. Seul le frontal publie, et sur la boucle locale

Le service de données n'a aucune raison d'être joignable depuis l'extérieur
de la pile. Et la façade ne doit l'être qu'à l'adresse et sur le port que le
fichier d'environnement fourni déclare.

### 4. Une donnée écrite avant une recréation est servie après

**C'est l'exigence critique : elle n'est compensée par aucun total.** C'est la
seule chose qu'une composition perd pour de bon : un service se relance, un
réseau se recrée, un port se republie, mais une donnée écrite dans la couche
d'un conteneur part avec lui.

Le contrôle écrit un témoin, recrée la pile et relit la façade. Il n'impose
aucun nom de volume : seul l'effet compte. Un volume anonyme n'est pas
rattaché à un service recréé, et se voit donc ici.

### 5. La composition résolue ne porte aucune variable en suspens

`docker compose config` rend la composition **telle que le moteur la
comprend**, variables substituées. Une variable absente sans valeur par défaut
y devient une chaîne vide : Compose **avertit**, et il **accepte quand même**.
La pile démarre donc en écoutant sur un port que personne n'attend, et
l'avertissement part sur la sortie d'erreur, là où un script ne le lit pas.

Et au moins une valeur doit venir d'une **interpolation** : le lab fournit un
`.env`, et une composition qui recopie ses valeurs à la main ne s'en sert pas.

## Ce que l'épreuve ne demande pas

Ni sonde de santé, ni condition de dépendance. Elles s'enseignent au module
suivant, et le frontal fourni réessaie son amont : l'ordre de démarrage est
indifférent.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points**.
