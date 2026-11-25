# Écrire une politique qui refuse par défaut

## La situation

Sur `docker.lab`, le `worker` du projet `dsoxlab-securite-apparmor` crée deux
fichiers en mode 444, `/lab/public.txt` et `/lab/private.txt`. Les droits Unix
laissent lire les deux. Le service est `unconfined`, et aucun profil n'est chargé
pour lui. Le projet se trouve dans `/opt/dsoxlab-securite-apparmor`, avec
`profile.modele`, un modèle à compléter.

## Mission

1. **Écrivez** le profil `dsoxlab-securite-apparmor` à partir de
   `profile.modele`, **chargez-le**, et attachez-le à `worker`.
2. PID 1 annonce ce profil en mode `enforce`.
3. `/lab/public.txt` renvoie `public`. `/lab/private.txt` reste en mode 444, et
   sa lecture échoue avec Permission denied.
4. Le profil **refuse par défaut** : ni `file,`, ni `capability,`, ni `network,`
   sans précision. Le contrôle essaie de lire `/etc/shadow` depuis le conteneur.

**Le refus vient d'une omission, pas d'une règle `deny`** : un `deny` s'applique
aussi en `complain`, et ne prouverait rien du mode appliqué. Le service doit
pouvoir créer `/lab/private.txt` : accordez-lui l'écriture, pas la lecture.

## La méthode

Chargez le profil en `complain`, démarrez le service, et relevez ce que le noyau
aurait refusé. En `complain`, il le note `ALLOWED` :

```bash
sudo dmesg | grep 'apparmor="ALLOWED"'
```

Ajoutez la règle correspondante, recommencez, puis retirez `complain` et
rechargez. Une fois en `enforce`, un refus se lit `DENIED`.

Cette méthode montre ce que le service a tenté. Elle ne montrera pas ici
`signal (receive) peer=runc,`, parce que ce PID 1 ignore SIGTERM. Mettez-la quand
même : sans elle, `docker stop` ne peut pas arrêter proprement un service qui
traite ce signal.

Gardez le projet et l'étiquette `dsoxlab.lab=securite-apparmor`. Ne modifiez aucun
autre profil, ne désactivez pas AppArmor et ne touchez pas à `/etc/apparmor.d` :
un profil chargé par `apparmor_parser` vit jusqu'à ce qu'on le retire, et le
nettoyage ne retire que celui de ce lab.
