# epreuve-reprendre-un-hote-docker : l'épreuve du module d'administration

## Ce que cette épreuve éprouve

Reprendre une machine dont personne ne s'occupait, sans casser ce qui y tourne
ni perdre ce qu'elle porte. Elle clôt le module « Administrer le démon » et ne
réexplique rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## Pourquoi cette épreuve a été éprouvée avant d'être écrite

C'est le setup le plus intrusif du catalogue : il touche le **démon**, **systemd**
et les **comptes**, et non de simples conteneurs. Une réserve avait donc été
posée avant de l'écrire : si son cycle ne rendait pas une machine propre, elle ne
serait pas livrée.

Deux gestes ont été éprouvés séparément, sur un banc qui les posait puis les
retirait :

- **ouvrir une API TCP sans TLS**, par surcharge systemd, puis la retirer et
  vérifier que le démon repart. Le piège est connu : un `hosts` dans
  `daemon.json` alors que systemd passe déjà `-H fd://` fait **refuser le
  démarrage** au démon. Cela aurait cassé la machine au lieu de poser un défaut ;
- **filtrer par méthode HTTP** devant le socket, et constater `200` sur une
  lecture et `403` sur un arrêt.

Le banc a conclu, et c'est à cette condition que l'épreuve existe.

## Les quatre défauts, et ce qu'ils enseignent

| Défaut | Ce qu'il enseigne |
| --- | --- |
| aucune rotation des journaux | le défaut du pilote `json-file` est d'écrire sans limite, et un conteneur bavard remplit le disque |
| images pendantes et cache de build | ce qu'un hôte non suivi accumule sans que personne ne le voie |
| un compte parti encore dans `docker`, un outil qui monte le socket | être dans ce groupe, ou parler au socket, c'est pouvoir tout faire sur l'hôte |
| l'API ouverte en TCP sans TLS | la faute la plus grave : un conteneur privilégié, et l'on est root |

## L'exigence critique, et pourquoi c'est le meilleur piège du catalogue

**Perdre le volume de l'application fait échouer l'épreuve**, même à 80 points.

Il est bon parce qu'il ne se déclenche pas sur une faute d'inattention, mais sur
**le geste qui semble le plus raisonnable** : pour rendre de la place, on tape
`docker system prune`, et l'une de ses options emporte les volumes. L'apprenant
qui le fait a raison sur l'intention et tort sur la portée.

Le contrôle compare la **donnée**, pas l'existence du volume : un volume recréé
vide porte le bon nom et ne vaut rien.

## Ce que les contrôles mesurent, et ce qu'ils ne mesurent pas

Le brief parlait d'un « espace libre au-dessus du seuil ». Un seuil absolu
n'aurait rien voulu dire sur cette machine, qui a vingt gigaoctets dont quatorze
libres : le lab ne peut pas remplir un disque sans risquer de le remplir pour de
bon.

Le contrôle mesure donc ce qui est vraiment en jeu et vérifiable : les objets
récupérables ont été rendus, et le volume utile est resté. C'est la compétence,
et non le chiffre.

## Ce que ce lab rend à la machine

Tout ce qu'il change, il le relève avant dans `/root/.lab-reprise-state.json`, et
le `cleanup` le remet comme il l'a trouvé : le contenu exact de `daemon.json`
s'il existait, son absence sinon, la surcharge systemd retirée, le répertoire de
surcharges retiré **s'il n'existait pas avant**, le démon redémarré sur cette
configuration rendue, les deux comptes du lab supprimés, et le groupe `docker`
restitué.

Le démon est remis en marche **avant** tout le reste, parce que le cycle de
validation interroge le moteur après le nettoyage : un démon muet ne donne pas
un écart, il donne une absence de mesure.

## Ce que l'épreuve ne mesure pas

Le mode rootless, et le durcissement de l'exécution : c'est le sujet de
`epreuve-durcir-sans-casser`.
