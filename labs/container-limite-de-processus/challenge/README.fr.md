# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-container-limite-de-processus`.

1. Gardez un `worker` actif, projet `dsoxlab-container-limite-de-processus`,
   label `dsoxlab.lab=container-limite-de-processus`.
2. Fixez le plafond pids à 16 exactement ; `pids.max` doit concorder.
3. Gardez une limite mémoire positive de 64 Mio maximum et le garde-fou CPU.
4. Une rafale finie doit incrémenter max dans `pids.events`, sans tuer le
   worker ni provoquer d'OOM.

Le contrôle effectue lui-même la rafale protégée. Aucun stress non borné.
