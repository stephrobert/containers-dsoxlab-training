# Un programme qui rend root à un compte ordinaire

## La situation

Sur `docker.lab`, le `worker` du projet `dsoxlab-securite-no-new-privileges`
démarre sous l'UID 1000. Son image contient `/usr/local/bin/identity`, un
programme setuid de root qui affiche l'UID réel et l'UID effectif. Lancé par le
worker, il affiche `1000:0` : il a obtenu root. Le projet se trouve dans
`/opt/dsoxlab-securite-no-new-privileges`.

## Mission

Empêchez ce gain dans le service, sans toucher au programme :

1. la barrière est déclarée sur le conteneur ;
2. PID 1 annonce `NoNewPrivs: 1` ;
3. `identity`, lancé sous l'UID et le GID 1000, affiche `1000:1000`.

Le programme garde son propriétaire root et le mode 4755. Gardez le projet,
l'étiquette `dsoxlab.lab=securite-no-new-privileges` et les limites de
ressources. Ne modifiez ni l'hôte ni le démon.
