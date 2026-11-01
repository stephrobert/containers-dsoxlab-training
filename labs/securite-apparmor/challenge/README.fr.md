# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-securite-apparmor`.

1. Gardez `worker` actif dans le projet `dsoxlab-securite-apparmor`,
   label `dsoxlab.lab=securite-apparmor`.
2. Attachez le profil déjà chargé `dsoxlab-securite-apparmor` en mode enforce.
3. `/lab/public.txt` doit toujours renvoyer `public`.
4. `/lab/private.txt` doit rester en mode 444, mais sa lecture doit échouer avec
   Permission denied.

Seul ce nouveau profil est concerné. Ne rechargez aucune politique existante.
