# Épreuve : mettre un service en marche

Ce poste a été « installé » par quelqu'un qui est parti. Le moteur est présent,
rien ne tourne, et deux conteneurs arrêtés traînent, issus de la même image.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. Le moteur tourne, il est activé, et le compte lui parle

**Trois faits, et un seul geste ne les règle pas.** « Démarré » et « activé »
sont distincts : seul le second survit au prochain redémarrage. Et parler au
moteur n'est pas la même chose que le démarrer.

### 2. Le service tourne et rend la valeur demandée

Un conteneur nommé `annuaire`, en marche, issu de `lab-mise-en-marche:1.0`, dont
la **réponse** porte la valeur que la machine indique. La valeur est lue dans la
réponse du service, **pas dans son environnement** : une variable posée sur un
conteneur qui ne s'en sert pas ne prouve rien.

### 3. L'ancien conteneur homonyme a disparu

Un seul conteneur porte ce nom, et c'est celui qui tourne.

### 4. Le témoin est conservé, arrêté, et ses journaux lisibles

**C'est l'exigence critique : elle n'est compensée par aucun total.**
`journal-de-bord` doit rester présent, **arrêté**, et ses journaux doivent
toujours se lire. L'énoncé le demande « tel quel » : le relancer n'est pas
anodin, parce qu'un conteneur qui repart peut écraser ce qu'il portait.

### 5. La prédiction annonce le programme et les arguments effectifs

Deux lignes dans `/opt/lab-mise-en-marche/prediction.txt`, **écrites sans jouer
la commande**. Le contrôle ne compare pas à des valeurs figées : il recrée le
conteneur décrit, sans le démarrer, lit ce que le moteur en a retenu, puis le
retire. Votre prédiction est donc mesurée contre le moteur lui-même.

## Ce qui est fourni

L'image `lab-mise-en-marche:1.0` porte le service. Rien à construire. Elle lit
la variable d'environnement `SALLE`, et son point d'entrée accepte un argument
de mode.

Ni volume ni port publié : ce n'est pas le sujet.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
