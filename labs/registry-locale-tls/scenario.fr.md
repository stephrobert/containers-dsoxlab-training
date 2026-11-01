# Le registre répond, mais Docker ne lui fait pas confiance

Sur `docker.lab`, `dsoxlab-tls-registry` sert déjà une image dans son stockage,
mais seulement en HTTP. Le nom `registry-tls.lab.test` désigne **l'adresse
réseau de la VM**, port `15443`, pas la boucle locale. Docker refuse donc le
registre tant que TLS et sa confiance ne sont pas configurés.

L'atelier `/opt/lab-registry-tls` contient :

- `config.yml`, monté dans `/etc/docker/registry/config.yml` du conteneur ;
- `certs/server.crt` et `certs/server.key`, montés dans `/certs` ;
- `certs/ca.crt`, l'autorité privée qui a signé le certificat ;
- `data/`, le stockage existant, à conserver.

## Mission

- Configurez TLS avec le certificat fourni et redémarrez le registre.
- Installez la CA dans le répertoire de confiance Docker propre à
  `registry-tls.lab.test:15443`.
- Faites réussir `docker pull registry-tls.lab.test:15443/catalogue/appli:1.0`.
- Exécutez cette image sans réseau ; elle affiche la release préparée.
- L'API `/v2/` ne doit plus répondre avec succès en HTTP.
- Le certificat doit être vérifié ; ni exception `insecure-registries`, ni
  `curl -k`, ni changement de résolution vers la boucle locale ne convient.

Pour observer la chaîne présentée :

```bash
curl --noproxy '*' --cacert /opt/lab-registry-tls/certs/ca.crt \
  https://registry-tls.lab.test:15443/v2/
```

Le nom du répertoire Docker inclut le port. Un pull se fait par le moteur
Docker, pas par votre terminal : une CA ajoutée seulement à curl ne suffit pas.
Le lab est limité au réseau privé des VM et ne contacte aucun registre public
pour les contrôles. Ne modifiez pas le produit, la CA ou les fichiers du banc.
