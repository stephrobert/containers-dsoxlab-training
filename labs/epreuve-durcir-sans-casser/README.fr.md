# epreuve-durcir-sans-casser : l'épreuve du module de durcissement

## Ce que cette épreuve éprouve

Retirer à un service ce dont il n'a pas besoin, sans lui retirer ce dont il a
besoin. Elle clôt le module « Durcir l'exécution » et ne réexplique rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et **deux** sont critiques : c'est la seule
épreuve du catalogue dans ce cas.

## Deux mesures ont fondé cette épreuve, et elles contredisent un conseil répandu

**`NET_BIND_SERVICE` ne sert à rien dans un conteneur Docker.** Mesuré le
2026-11-02 : un conteneur sans AUCUNE capability écoute parfaitement sur le port
80. La raison est que le démon pose `net.ipv4.ip_unprivileged_port_start = 0`
dans le conteneur, ce qui rend tous les ports « non privilégiés ». Le conseil
« tout retirer sauf NET_BIND_SERVICE », que l'on lit partout, ne retire donc rien
d'utile et n'ajoute rien.

**La capability qui discrimine ici est `CHOWN`.** Mesuré sur le service de ce
lab : sans elle il sort en 77, avec elle seule il démarre, et `DAC_OVERRIDE` ne
suffit pas. Le service en a besoin parce qu'il ajuste au démarrage le propriétaire
de son répertoire de données, ce qu'une image fait couramment quand ses données
viennent d'un volume dont l'UID ne correspond pas.

Le premier dessin de l'épreuve reposait sur `NET_BIND_SERVICE`. Le contrôle
aurait alors passé sans qu'aucune capability soit nécessaire, et l'épreuve aurait
enseigné une fausseté.

## Pourquoi le contrôle n'impose aucune capability par son nom

Parce qu'il note l'état final. Il mesure que le jeu est **réduit** et que le
service **tourne**. Un apprenant qui se passe de `CHOWN` autrement, en préparant
les droits du volume avant le lancement par exemple, a mieux durci : exiger le
nom de la capability punirait la meilleure réponse.

## Les deux exigences critiques, et pourquoi deux

**Le secret lisible dans l'environnement**, et **le pare-feu désactivé**. Les deux
sont des portes ouvertes. Un barème qui laisserait compenser une porte ouverte par
du travail fait ailleurs délivrerait une attestation sur une installation
vulnérable, ce qui est le contraire de ce que cette épreuve existe pour mesurer.

La seconde est la fausse correction la plus tentante du catalogue, et elle est
parfaitement rationnelle du point de vue de qui la commet : le flux ne passe pas,
le pare-feu bloque, on retire le pare-feu. Le symptôme disparaît en une commande.

## Le contrôle du pare-feu vérifie que la protection AGIT

Lire la règle ne suffit pas. Une règle de blocage placée **après** une règle
d'acceptation qui matche d'abord est toujours écrite et ne fait plus rien : dans
une chaîne, l'ordre décide. Le contrôle essaie donc le port protégé, en plus de
lire la table.

C'est la même exigence que partout dans ce catalogue : on mesure ce qui agit, pas
ce qui est déclaré.

## Ce que ce lab touche sur la machine, et ce qu'il rend

Il pose une **table nftables dédiée**, et c'est le geste le plus risqué du
catalogue : une règle mal cadrée coupe SSH, et le validateur perd sa cible. Trois
précautions, toutes mesurées sur un banc avant l'écriture :

- la table est **dédiée au lab** et ne vise que deux ports de test. Le 22 n'est
  jamais touché ;
- le cleanup la retire **par son nom**, jamais par un `flush` : les règles de
  Docker vivent dans d'autres tables, et les emporter couperait le réseau des
  conteneurs ;
- le cleanup **vérifie** que la table est partie, et échoue en le disant sinon :
  une machine laissée filtrée casserait les labs suivants en silence.

## Ce que l'épreuve ne mesure pas

seccomp et AppArmor. Ce sont des sujets à part entière, et les mesurer ici aurait
fait une épreuve de deux heures.
