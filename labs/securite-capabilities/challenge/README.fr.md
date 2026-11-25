# Un service qui s'arrête quand on lui retire tout

Un petit lanceur de travaux a été déployé avec les capabilities par défaut de
Docker. Il exécute chacun de ses travaux dans une **cellule** : un répertoire
dans lequel il confine le travail avec `chroot`. Il rend compte de son état
chaque seconde dans `/run/lanceur/etat`.

La revue de sécurité demande le moindre privilège, et le conseil est connu :
retirer toutes les capabilities, puis rendre celles dont le service a besoin.
Personne ne sait laquelle c'est. Tout retirer et relancer ne suffit pas : **le
lanceur s'arrête au démarrage**.

Seul ce projet jetable est concerné. Ne modifiez pas le démon, n'utilisez pas le
mode privilégié, et ne touchez à aucun autre conteneur.

## Mission

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-securite-capabilities`.

1. Gardez un service Compose `worker` actif, projet
   `dsoxlab-securite-capabilities`, label `dsoxlab.lab=securite-capabilities`.
2. Retirez TOUTES les capabilities et rajoutez-en **exactement une** : celle dont
   le lanceur a besoin. Le conteneur n'est pas privilégié.
3. Le lanceur doit tourner : son rapport dans `/run/lanceur/etat` dit `ok`, et le
   nombre qui suit continue de monter.
4. PID 1 doit porter cette seule capability dans son masque effectif, et aucune
   autre.
5. Conservez le fichier `/proof`, à root : lui donner l'UID 123 doit échouer.

Trouvez laquelle en lisant ce que le lanceur dit quand il s'arrête : ses
journaux nomment l'opération refusée. Ne la devinez pas dans une liste.

Conservez l'image épinglée et les ressources bornées. Utilisez Compose v2 ou
`docker-compose` avec le nom de projet explicite. Aucune modification du démon.
