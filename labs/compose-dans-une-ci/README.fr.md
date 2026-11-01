# Compose dans une CI locale

Challenge, c4, 45 minutes. Lire [la mission](scenario.fr.md).
Exécuter de vrais tests sans runner hébergé ; l'évaluation mesure les codes
de sortie, la source commitée reconstruite et le nettoyage en succès comme en
échec. Les archives acceptées sont rechargées et reliées à la révision OCI,
au commit réel et au SHA-256 ; ni échec ni source non commitée n'en publie.

Runtime : VM Debian 13, Docker, BuildKit, Compose v2 (`up --wait`), Python 3,
Git, shell POSIX et `timeout`. Le setup télécharge les paquets et une base Python
épinglée ; la CI est ensuite hors ligne. Seuls `/opt/lab-compose-ci` et les
objets labellisés du lab sont retirés. Aucun prune global ni Docker du poste.
Les ID de bases préexistantes sont relevés avant les pulls ; seules les bases
introduites et non partagées sont retirables, sans force ni suppression de parents.
Référence chiffrée : `solution/compose-dans-une-ci/solution.yaml`.
