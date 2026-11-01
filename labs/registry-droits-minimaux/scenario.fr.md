# Des identifiants ne sont pas des permissions

L'équipe de livraison dispose d'un registre TLS et de deux comptes valides,
mais aucun ne peut distribuer une image. Donner les droits administrateur
aux deux ferait du serveur de déploiement un éditeur.

Rétablissez le chemin de livraison sans élargir sa frontière. L'éditeur
travaille sur `docker.lab` ; le lecteur utilise le moteur distinct de
`docker-client.lab`. Un produit nouvellement publié doit arriver intact par
son digest immuable, et le lecteur doit rester incapable d'uploader.

Travaillez dans `/opt/lab-registry-rights` sur les VM, pas dans un répertoire
local. Consultez [les exigences](challenge/README.fr.md).
