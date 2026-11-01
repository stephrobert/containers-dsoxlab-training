# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-troubleshoot-disque-plein`.

1. Gardez le `worker` existant actif, projet `dsoxlab-troubleshoot-disque-plein`,
   label `dsoxlab.lab=troubleshoot-disque-plein`.
2. Préservez `/sandbox` en tmpfs de 16 Mio et le plafond mémoire de 64 Mio sans swap.
3. Retirez seulement `/sandbox/fill.bin` ; gardez `/sandbox/keep.txt` et son
   contenu `keep-this-receipt`.
4. Une vraie écriture de 1 Mio doit réussir dans `/sandbox`.

Ni recréation, redimensionnement, écriture hôte ni prune global. Le contrôle
retire sa propre sonde d'écriture finie dans tous les cas.
