# Mesurer les contrôles cgroup effectifs

Trois contrôles inspectent les limites mémoire/processus/CPU, lancent un essai CPU
borné et recréent le worker pour refuser des limites seulement manuelles.
Le setup exige cgroup v2 ; un hôte incompatible échoue plutôt que skipper.
Aucun OOM ni épuisement de processus n'est provoqué.
