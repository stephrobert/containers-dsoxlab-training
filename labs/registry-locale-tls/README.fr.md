# TLS présenté, confiance installée, pull vérifié

Le registre part en HTTP avec un produit déjà publié. La CA et le certificat
sont tirés au setup ; aucune identité privée n'est versionnée.

Le nom pointe sur l'adresse réseau de la VM : la boucle locale est
implicitement insecure dans Docker et ne pourrait pas prouver ce lab.
Les contrôles vérifient HTTPS avec la CA, le refus d'un mauvais nom,
l'absence de réponse HTTP réussie, le vrai pull et son produit.
Ils refusent une entrée `RegistryConfig.IndexConfigs` explicitement insecure.
Surtout, ils retirent temporairement la CA propre au registre et exigent que
le pull échoue avec une erreur X.509, puis restaurent la CA. Cette mesure
détecte aussi une exception insecure par CIDR ou une résolution vers la boucle
locale. Les registres sécurisés ordinaires ne figurent pas forcément dans
`IndexConfigs` : une entrée absente ne suffit pas à conclure.

Chaque contrôle exige d'abord HTTPS : aucun ne récompense l'état initial.
Le nettoyage retire seulement le registre, ses images étiquetées, sa résolution
de nom et son répertoire de confiance, sans redémarrer le démon Docker.
