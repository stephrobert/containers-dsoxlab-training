# Écrire une politique qui refuse par défaut

Le worker contient deux fichiers en mode 444 : les permissions Unix autorisent
les deux lectures. Aucun profil AppArmor n'est chargé pour ce lab, et le starter
est `unconfined`.

Dans `/opt/dsoxlab-securite-apparmor`, **écrivez le profil, chargez-le et
attachez-le** à `worker`. `profile.modele` est un modèle qui porte le nom imposé
et la méthode ; complétez-le. Gardez `/lab/public.txt` lisible et rendez
`/lab/private.txt` illisible **par la politique obligatoire, pas par chmod** :
les deux fichiers doivent rester en mode 444.

**Refusez par omission, et non par une règle `deny`.** Un `deny` explicite
s'applique même en mode `complain` : un profil bâti ainsi rend le même verdict
dans les deux modes et ne prouve rien de celui qui est appliqué. Une permission
que vous ne nommez jamais n'est refusée qu'en `enforce`, puisque `complain`
permet et journalise tout ce qui n'est pas autorisé. Le service doit créer
`/lab/private.txt` : accordez l'écriture et ne nommez jamais la lecture.

**Une politique nomme ce dont le service a besoin et refuse le reste.** Une
règle `file,` nue, ou une règle `capability,` ou `network,` nue, autorise tout et
fait du profil une liste noire d'une ligne. Le lab le vérifie en lisant
`/etc/shadow`, qu'un service manipulant deux fichiers de `/lab` n'a aucune raison
de lire.

La méthode est la vraie, et le modèle la détaille : charger en `complain`,
démarrer le service, relever les refus journalisés par le noyau avec
`dmesg | grep 'apparmor="DENIED"'`, ajouter la règle correspondante, recommencer,
puis retirer `complain` et recharger.

Ne modifiez aucun autre profil, ne désactivez pas AppArmor, ne laissez pas le
profil en `complain` et ne touchez pas à `/etc/apparmor.d` : un profil chargé par
`apparmor_parser` vit jusqu'à ce qu'on le décharge, et le nettoyage ne retire que
celui que ce lab possède.
