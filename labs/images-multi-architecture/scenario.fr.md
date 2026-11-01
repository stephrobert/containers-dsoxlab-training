# Une release, deux exécutions réelles

La release n'a pas encore d'index multi-plateforme exploitable. Travaillez dans
`/opt/lab-multiarch` sur `docker.lab` ; la VM jetable fournit Go et QEMU.
Publiez `127.0.0.1:15318/workshop/probe:release` avec exactement deux variantes
Linux distinctes : AMD64 et ARM64. Le programme fourni doit calculer le carré
d'un entier nouveau et refuser les entrées invalides sur les deux plateformes.

Un manifeste marqué ARM64 ne prouve pas que son exécutable est ARM64. Les
tests résolvent les manifestes depuis l'index, tirent par digest de manifeste
et exécutent chaque variante, puis vérifient
l'architecture réelle du binaire et son résultat. AMD64 est natif ; ARM64
s'exécute sous QEMU dans cette VM AMD64. C'est une attestation runtime émulée,
pas une qualification de matériel ARM64 natif ni une mesure de performance.

N'installez ni Docker ni QEMU sur votre poste. N'exposez pas le registre
d'atelier limité à la boucle locale et ne supprimez pas les objets d'autres labs.
