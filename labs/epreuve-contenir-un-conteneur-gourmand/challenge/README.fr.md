# Le traitement qui emporte la machine avec lui

Le conteneur `traitement` exécute un traitement par lots. La nuit, il s'emballe :
la machine entière ralentit, il finit par se faire tuer, et il laisse derrière
lui des fichiers incomplets. Au matin, personne ne sait ce qui a été traité.

Il écrit ses résultats dans `/resultats`, porté par le volume
`dsoxlab-gourmand-resultats`. **Ce volume contient déjà des résultats, et ils ne
se reproduisent pas.**

## Ce qui est attendu à la fin

1. Le conteneur porte **trois limites**, visibles dans son inspection **comme
   dans son cgroup** : la mémoire, le processeur, et le nombre de processus.
2. Quand la pointe est déclenchée, elle est **contenue** : le conteneur ne
   dépasse pas sa propre limite mémoire, et **aucun processus de l'hôte n'est
   tué**.
3. Le traitement **répond encore** après la pointe.
4. Les résultats antérieurs sont **intacts**, et aucun fichier de `/resultats`
   n'est tronqué : chacun porte sa ligne de fin.
5. Le fichier `/opt/lab-gourmand/releve.txt` consigne deux faits, une ligne
   chacun :

   ```text
   pid_hote=<le PID, sur l'hôte, du processus PID 1 du conteneur>
   runtime=<le runtime par défaut du moteur>
   ```

**Pour déclencher la pointe** : créez le fichier `/tmp/pointe` **dans** le
conteneur, puis adressez-lui une requête. Le traitement l'évalue après chaque
requête servie. C'est un outil du lab, pas une énigme.

L'énoncé complet est aussi sur la machine, dans `/opt/lab-gourmand/MISSION.md`.

## Une précision sur la pointe

Elle est **bornée**, et deux chiffres la décrivent sans se confondre. La chaîne
allouée pèse **268 Mo** ; la mémoire que le cgroup voit consommer monte à
**404 Mo**, parce que le doublement fait détenir l'ancienne chaîne et la nouvelle
au même instant. Mesuré le 2026-11-04.

Dans les deux cas la machine garde sa marge, et c'est délibéré : une épreuve ne
doit pas pouvoir emporter la machine qui la mesure.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune valeur de
limite n'est imposée : ce qui est mesuré est qu'une limite existe, qu'elle soit
appliquée par le noyau, et qu'elle contienne la pointe sans tuer le service.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**perdre les résultats antérieurs fait échouer l'épreuve**, même avec tout le
reste en place. C'est le piège, et il reste entier sans fausse contrainte :
recréer le conteneur est **une** voie de pose des limites, et c'est celle où l'on
oublie un volume. L'autre voie existe, et la trouver fait partie du travail.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.

## Épreuve : contenir un conteneur gourmand

Le conteneur `traitement` s'emballe la nuit, ralentit la machine, se fait tuer,
et laisse des fichiers incomplets. Il écrit dans `/resultats`, porté par un
volume **qui contient déjà des résultats**.

### Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

#### 1. Trois limites, posées et appliquées

Mémoire, processeur, nombre de processus. Chacune est lue à **deux endroits** :
l'inspection dit ce que le moteur a **retenu**, le cgroup dit ce que le noyau
**applique**. Les deux peuvent différer, et c'est pourquoi les deux sont lues.

Une précision qui change l'ordre de vos gestes : **deux voies** posent ces
limites, et les deux marchent. Recréer le conteneur, ou `docker update` sur
celui qui tourne. Mesuré sur cette machine, Docker 29.9.2 : un `docker update
--memory 64m --memory-swap 64m --cpus 0.5 --pids-limit 50` rend 0, l'inspection
porte les nouvelles valeurs, le cgroup les applique (`memory.max=67108864`,
`pids.max=50`, `cpu.max=50000 100000`) et `StartedAt` ne change pas.

#### 2. La pointe est contenue

Lire une limite ne dit pas si elle contient quoi que ce soit. Le contrôle
déclenche la pointe, puis lit `memory.peak` et `memory.events` : le pic ne doit
pas dépasser la limite, et la limite doit avoir été **atteinte**, sans quoi la
pointe n'a pas eu lieu et le contrôle ne mesurerait rien.

Et l'hôte ne doit avoir perdu aucun processus. C'est le vrai sujet : un
conteneur sans limite ne se punit pas lui-même, **il punit son voisin**.

#### 3. Le traitement répond encore

**Contenir n'est pas tuer.** Une limite bien posée tue le processus gourmand,
pas le service. Ce contrôle est séparé du précédent parce que sa cause est
différente : il échoue avec une limite parfaitement posée mais trop basse.

#### 4. Les résultats antérieurs sont intacts, et rien n'est tronqué

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Le contrôle compare des **empreintes**, pas des noms : c'est ce qui distingue
« les fichiers sont là » de « les fichiers sont intacts ». Un volume recréé vide,
puis regarni par le traitement, porterait des noms plausibles et un contenu
différent.

#### 5. Le relevé dit le PID hôte et le runtime

Le PID hôte du PID 1 est la **jointure entre les deux mondes** : le processus qui
se croit numéro un dans son conteneur porte un autre numéro sur la machine, et
c'est celui-là qu'on voit dans `ps`, dans `top` et dans un journal du noyau. Qui
ne sait pas faire cette jointure ne peut pas rattacher une trace de l'hôte à un
conteneur.

Le contrôle **recalcule** les deux valeurs : il n'en garde aucune en dur.

### Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**. Aucune valeur de limite n'est imposée.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
