# Contenir la création de processus

Le worker démarre avec un plafond sûr de 32 tâches, mais son budget opérationnel
est de 16. Le plafond doit être une limite de cgroup, pas seulement un ulimit
de shell.

Dans `/opt/dsoxlab-container-limite-de-processus`, appliquez le budget de
16 tâches à `worker` dans le projet `dsoxlab-container-limite-de-processus`.
Gardez le service actif et les garde-fous mémoire et CPU.

Le contrôle lance au plus 24 enfants sleep de courte durée, uniquement après
vérification du plafond effectif. Ce n'est pas une fork bomb. Ni récursion,
ni boucle de fork non bornée, ni limite de processus globale sur l'hôte.
Après la rafale finie, le service original doit reprendre sans redémarrage ni
perte d'un reçu applicatif frais. Seul le reçu de l'essai est retiré.
