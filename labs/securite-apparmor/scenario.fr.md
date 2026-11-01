# Deux fichiers lisibles, un refus obligatoire

Le worker contient deux fichiers en mode 444. Les permissions Unix autorisent
les deux lectures. Un profil AppArmor dédié est déjà chargé, mais le starter
est unconfined et ne l'utilise pas.

Dans `/opt/dsoxlab-securite-apparmor`, confinez `worker` avec le profil existant
`dsoxlab-securite-apparmor`. Gardez `/lab/public.txt` lisible et rendez
`/lab/private.txt` illisible par la politique obligatoire, pas par chmod.

Ne modifiez aucun autre profil, ne désactivez pas AppArmor, n'utilisez pas
complain et ne modifiez pas `/etc/apparmor.d`. Cleanup retire seulement le
profil nouvellement créé pour ce lab.
