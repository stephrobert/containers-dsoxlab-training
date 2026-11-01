# Droits minimaux sur un registre

**Langue :** [English](README.md) · [Français](README.fr.md)

## Authentification et autorisation sont différentes

Une connexion réussie identifie un compte. Elle n'autorise pas toutes les
actions sur tous les dépôts. Distribution peut proposer un challenge Bearer ;
le client s'authentifie auprès du service de jetons, demande des scopes de
dépôt, puis présente le jeton signé au registre.

Le registre contrôle la signature, l'émetteur, l'audience et les actions
permises. Le service de jetons doit intersecter les actions demandées avec
une ACL administrée. Basic auth seule ne fournit pas ces rôles. Ici BCrypt
protège les mots de passe synthétiques dans le service de jetons, pas une
barrière htpasswd sans rôles devant le registre.

## Un exemple d'ACL neutre

Dans une configuration jetable étrangère à cette mission :

```yaml
acl:
  - match: {account: packager, name: workshop/widget}
    actions: ["pull", "push"]
  - match: {account: observer, name: workshop/widget}
    actions: ["pull"]
```

Dans docker_auth, les règles sont ordonnées et les demandes sans
correspondance sont refusées. Restreignez le dépôt et le compte. Un éditeur
a besoin de `pull` et de `push` : l'upload peut examiner les blobs existants.

## Prouver un transfert, pas un cache

Construisez un produit au contenu neuf, relevez son identifiant d'image et
son digest de registre, puis tirez ce digest sur un moteur distinct où
l'identifiant d'image est absent. Exécutez-le sans réseau et comparez sa
sortie. Tentez ensuite un upload avec le compte lecteur. Contrôlez aussi
l'ouverture d'une session d'upload : pousser des couches existantes ne
sollicite pas forcément toute la frontière d'écriture.

## Confiance et limites

La fixture utilise Distribution 2.8.3 et cesanta/docker_auth épinglés par
digest (le service d'autorisation cible Linux amd64). Les deux services
servent HTTPS réel sur l'adresse privée de la VM. La CA synthétique valable
deux jours est installée seulement dans le répertoire de confiance du
registre Docker ; aucune configuration de démon ni API Docker hôte n'est
exposée. Les jetons expirent après 60 secondes. C'est une petite ACL locale
statique, pas une fédération d'identités, une révocation ni un service Internet.

Seule l'ACL est à réparer ; le setup fournit TLS et les identifiants générés
à l'exécution. Chaque contrôle construit un produit neuf, sépare les dossiers
de connexion, refuse mauvais identifiants et nom TLS, puis retire
temporairement la CA pour prouver que Docker ne la contourne pas. Le nettoyage
restaure la confiance préexistante et retire seulement les images ajoutées,
les chemins et les conteneurs possédés par le lab.

[Mission](scenario.fr.md) · [Exigences](challenge/README.fr.md)
