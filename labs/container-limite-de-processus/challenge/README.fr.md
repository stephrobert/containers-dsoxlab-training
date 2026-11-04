# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-container-limite-de-processus`.

Gardez un `worker` actif dans le projet `dsoxlab-container-limite-de-processus`,
avec son label `dsoxlab.lab=container-limite-de-processus`. Le contrôle effectue
lui-même la rafale protégée ; n'exécutez aucun stresseur non borné.

Quatre contrôles indépendants mesurent quatre choses différentes.

## 1. Les limites déclarées portent le budget de tâches

`PidsLimit` vaut exactement 16, et la limite mémoire reste positive et au plus
égale à 64 Mio.

Le garde-fou mémoire est vérifié ici plutôt que dans un contrôle à lui, et c'est
délibéré : il est posé dès le départ, donc un contrôle séparé passerait avant
tout travail et donnerait des points pour rien. Borner les tâches ne doit pas
coûter le garde-fou mémoire, mais ce n'est pas une exigence qu'on satisfait, c'en
est une qu'on préserve.

## 2. Le cgroup applique vraiment le plafond de tâches

Dans le conteneur, `pids.max` vaut 16.

Le contrôle précédent lit ce qu'on a **demandé** au démon, celui-ci ce que le
noyau a **retenu**. C'est aussi ce qui distingue une limite de cgroup d'un
`ulimit` de shell : ce dernier ne lie que les descendants du shell qui l'a posé
et disparaît avec lui, si bien qu'il ne borne pas le service.

## 3. Une rafale bornée est refusée par le noyau

Vingt-quatre enfants `sleep` de deux secondes sont lancés, puis attendus. Le
compteur `max` de `pids.events` doit **augmenter**.

Ce n'est pas une fork bomb : ni récursion, ni boucle non bornée. Le nombre est
choisi pour dépasser 16 sans approcher les 32 du départ, et c'est mesuré : le
cgroup porte déjà trois tâches avant la rafale, donc 3 + 24 tient sous 32 et
déborde sous 16. Sous 32, le compteur reste à 0 ; sous 16, il passe à 1.

Un code de sortie non nul ne prouverait rien par lui-même. Seul ce compteur dit
que le noyau a refusé une création.

## 4. Le service survit à la saturation et garde son état

Trois choses, après une rafale que ce contrôle provoque lui-même : le worker
tourne encore, son `StartedAt` n'a pas changé, et un reçu écrit **avant** la
rafale se relit après.

Un plafond qui emporte le PID 1 à chaque pic ne protège pas le service, il le
remplace par un redémarrage. Et survivre comme processus ne suffit pas : un
service qui repart de zéro a perdu ce qu'il tenait.

Si le worker est à l'arrêt, le message donne son **code de sortie**, qui porte
le diagnostic : un 137 signifie que le noyau l'a tué pour la mémoire, et non
pour les tâches.

Le contrôle ne trie pas lui-même les deux causes, et c'est mesuré plutôt que
choisi. Un tri de ce genre serait du décor ici : sur cinq paliers de mémoire,
de 10 à 32 Mio, la rafale de vingt-quatre `sleep` n'a jamais provoqué d'OOM,
et sous le seuil de démarrage c'est le garde-fou du service actif qui refuse
avant. Vingt-quatre `sleep` busybox ne consomment presque rien.

Ce contrôle provoque **sa propre** rafale plutôt que de réutiliser celle du
contrôle 3, et il vérifie lui-même qu'une saturation a eu lieu : sans incident,
la survie ne se distingue pas du fait que rien ne s'est produit.

## Ce qui n'est pas noté, et pourquoi on vous le dit

Trois vérifications précèdent les mesures sans être des exigences : qu'un seul
`worker` tourne, qu'il porte son label, et que `pids.events` soit lisible. Sans
elles aucun contrôle ne peut observer quoi que ce soit, et un contrôle qui n'a
pas pu regarder ne doit jamais conclure au vert. Quand la lecture échoue sur un
service qui tourne, le message vous dit que ce n'est pas votre faute.
