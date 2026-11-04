# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-securite-apparmor`.

1. Gardez `worker` actif dans le projet `dsoxlab-securite-apparmor`,
   label `dsoxlab.lab=securite-apparmor`.
2. **Écrivez** le profil `dsoxlab-securite-apparmor` à partir de
   `profile.modele`, **chargez-le** vous-même, et attachez-le au service.
   Aucun profil n'est chargé au départ, et le starter est `unconfined`.
3. PID 1 doit annoncer ce profil en mode `enforce`, et non `complain`.
4. `/lab/public.txt` doit toujours renvoyer `public`.
5. `/lab/private.txt` doit rester en mode 444, mais sa lecture doit échouer avec
   Permission denied. **Le refus doit venir de l'omission de la permission de
   lecture, pas d'une règle `deny`** : un `deny` explicite s'applique aussi en
   `complain` et ne prouverait rien du mode appliqué.
6. Le profil doit **refuser par défaut** : aucune règle `file,` `capability,` ou
   `network,` nue. Le contrôle lit `/etc/shadow` depuis le conteneur, qu'un
   service manipulant deux fichiers de `/lab` n'a aucune raison de lire.

Seul ce nouveau profil est concerné. Ne rechargez aucune politique existante.
