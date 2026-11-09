# Un service qui s'arrête quand on lui retire tout

Un petit lanceur de travaux a été déployé avec les capabilities par défaut de
Docker. Il exécute chacun de ses travaux dans une **cellule** : un répertoire
dans lequel il confine le travail avec `chroot`. Il rend compte de son état
chaque seconde dans `/run/lanceur/etat`.

La revue de sécurité demande le moindre privilège, et le conseil est connu :
retirer toutes les capabilities, puis rendre celles dont le service a besoin.
Personne ne sait laquelle c'est. Tout retirer et relancer ne suffit pas : **le
lanceur s'arrête au démarrage**.

Dans `/opt/dsoxlab-securite-capabilities`, recréez le `worker` en marche pour
qu'il tourne de nouveau avec **une seule capability**, celle qui le fait
démarrer, et aucune autre. Gardez le projet `dsoxlab-securite-capabilities`, son
label de lab et `/proof`. Les contrôles lisent ce qu'on a demandé à Docker et ce
que le noyau applique à PID 1, lisent le rapport du lanceur lui-même, puis
tentent un changement de propriétaire inoffensif.

Seul ce projet jetable est concerné. Ne modifiez pas le démon, n'utilisez pas le
mode privilégié, et ne touchez à aucun autre conteneur.
