# Contrat 39 : réparer un flux routé de façon ciblée

[English](README.md)

1. Utilisez le projet `dsoxlab-reseau-pare-feu-cible-stack`, répertoire
   `/opt/dsoxlab-reseau-pare-feu-cible`. Gardez les deux réseaux bridge dédiés.
   Avant : `172.30.201.0/24`, arrière : `172.30.202.0/24`. Routeur `.254` sur chacun.
   Client autorisé : avant `.10`; non autorisé : avant `.20`; serveur : arrière `.10`.
2. Établissez les routes client et retour via le routeur. Sondez le contrôle
   routeur au port 8081, le saut routeur-serveur et les services locaux du
   serveur avant de conclure à une panne de routage ou de service.
3. Identifiez la règle du namespace responsable du défaut métier. Corrigez
   seulement le chemin métier TCP 8080, puis vérifiez la réponse HTTP
   `component: server`, `value: inventory-ready`.
4. Gardez INPUT/FORWARD en refus par défaut, retours established et règles
   `deny-untrusted`, `deny-debug`, `deny-rest`. Le client non autorisé ne
   joint pas TCP 8080; l'autorisé ne joint ni debug TCP 9090 ni le port fautif
   TCP 8089. Debug reste réellement à l'écoute sur le serveur.
   Les sondes négatives fraîches incrémentent les compteurs de refus concernés.
5. Recréez depuis la déclaration et répétez sondes autorisées et refusées.
   Ne modifiez ni serveur fourni ni code bootstrap.
6. Aucune modification du pare-feu poste/VM ou du forwarding global. NET_ADMIN
   seulement dans les conteneurs posant leurs routes; ni privilégié, réseau/PID/IPC
   hôte, montages hôte/socket API ou ports publiés. Gardez préfixes et labels.

Verdict unique : zéro avant correction, plein après, mesurés deux fois sur
`docker.lab` le 2026-11-01. Retirer tout le pare-feu échoue sur chemins négatifs, politiques et
compteurs. L'explication relève de la [revue humaine](review.fr.md) séparée.
