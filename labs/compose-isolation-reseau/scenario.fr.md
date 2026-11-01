# Une API relie deux zones de confiance

Trois images locales sont prêtes sur `docker.lab`, mais aucun conteneur ne tourne :

- `dsoxlab-compose-net:front` relaie `/cgi-bin/value` vers `http://api:8080/cgi-bin/value` ;
- `dsoxlab-compose-net:api` relaie `/cgi-bin/value` vers `http://data:8080/value.txt` ;
- `dsoxlab-compose-net:data` sert `/value.txt` sur le port `8080`.

## Mission

Écrivez `/opt/lab-compose-net/compose.yaml`, projet `dsoxlab-isolation-reseau`.
Déclarez exactement trois services nommés `front`, `api` et `data` avec leurs images
et commandes fournies, sans montages, mode privilégié ni capacités supplémentaires.

Créez deux réseaux bridge gérés par Compose :

- un réseau de façade non interne partagé uniquement par `front` et `api` ;
- un réseau de données interne partagé uniquement par `api` et `data`.

Ne raccordez aucun réseau supplémentaire. Publiez seulement `front` sur
`127.0.0.1:18088:8080`. Ni l'API ni les données ne doivent publier de port hôte.
L'adresse `http://127.0.0.1:18088/cgi-bin/value` doit relayer les données actuelles
via l'API. L'accès direct de `front` à `data:8080` doit échouer, y compris avec
l'adresse IP du conteneur de données plutôt que son nom DNS.

Gardez la découverte par nom ; ne fixez pas d'adresses IP et ne modifiez pas
le pare-feu global de Docker. La déclaration doit recréer tous les services
sans constructions, téléchargements ni étapes manuelles. Les contrôles changent
temporairement les données, les restaurent et répètent l'essai d'isolation
après recréation forcée de l'application.

`internal: true` limite la connectivité externe du réseau de données ; il ne
remplace pas la séparation des raccordements. L'API raccordée aux deux zones
peut accéder aux deux : cette topologie ne protège pas contre une API compromise.
