# Un registre privé, pas simplement chiffré

Le setup fournit une confiance TLS fraîche et un produit, mais ni contrôle
d'accès ni connexion Docker. Les identifiants sont tirés à chaque passage et
jamais versionnés. Ce lab est autonome, sans dépendance à l'état du lab TLS.

Trois contrôles mesurent le refus anonyme et des mauvais identifiants, la
récupération avec la connexion enregistrée et l'aller-retour d'un produit neuf :
push, suppression locale, pull. Tous commencent par exiger le contrôle
d'accès ; le score initial est donc nul. Retirer temporairement la CA propre au
registre doit faire refuser TLS par Docker ; elle est restaurée même en échec.

Le client dédié évite de modifier les identifiants Docker globaux préexistants.
Le nettoyage retire seulement les objets nommés et les images étiquetées,
intermédiaires comprises ; les données utilisent un répertoire hôte, pas un
volume anonyme. Aucune exception insecure globale n'est nécessaire.
