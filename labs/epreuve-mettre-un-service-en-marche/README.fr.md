# epreuve-mettre-un-service-en-marche : l'épreuve du module de prise en main

## Ce que cette épreuve éprouve

Rendre un poste utilisable, puis y faire tourner un service nommé et configuré,
sans détruire ce qui doit être préservé. Elle clôt le premier module et ne
réexplique rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## Les quatre obstacles posés, dits nulle part dans l'énoncé

| Obstacle | Symptôme visible | Ce qu'il enseigne |
| --- | --- | --- |
| le service est arrêté **et désactivé** | rien ne tourne, et rien ne reviendrait au reboot | « démarré » et « activé » sont deux faits distincts |
| le compte n'est plus dans le groupe `docker` | le démon est annoncé injoignable | un refus de permission ressemble à une panne du démon |
| un conteneur **arrêté** occupe le nom demandé | le `docker run` échoue sur un conflit de nom | un conteneur arrêté garde son nom |
| un conteneur témoin, arrêté lui aussi | il ressemble à l'obstacle précédent | ce qui gêne et ce qui ressemble à ce qui gêne ne sont pas la même chose |

Le deuxième obstacle est le plus instructif du lot : le message qu'il produit
désigne le démon, alors que la cause est dans les groupes du compte. C'est la
confusion qui fait perdre le plus de temps à qui débute.

## L'exigence critique, et pourquoi elle est là

**Supprimer ou redémarrer `journal-de-bord` fait échouer l'épreuve**, même à 80
points. Ce conteneur ressemble à l'obstacle à s'y tromper : arrêté, issu de la
même image, créé avant lui, donc premier dans un tri par date. La différence est
qu'il porte la trace d'un incident, et que l'énoncé demande de le conserver.

C'est la situation réelle que cette exigence reproduit : le conteneur qu'un
`docker rm` trop large emporte est celui qui portait la trace. Un barème qui
laisserait compenser cette perte délivrerait une attestation à quelqu'un qui
détruit des preuves.

Il doit rester **arrêté**, et pas seulement présent : le relancer peut écraser
ce qu'il portait, et « tel quel » veut dire tel quel.

## Le cinquième contrôle, et pourquoi il recalcule la vérité

Prédire `.Path` et `.Args` avant de lancer la commande, c'est prédire ce que le
moteur garde d'un ENTRYPOINT et ce qu'un argument de ligne de commande remplace.
Le contrôle ne compare pas la réponse à des valeurs écrites dans le test : il
**crée le conteneur décrit, sans le démarrer**, lit ce que le moteur en a retenu,
puis le retire sous un nom unique.

Deux raisons. La première est de ne pas figer dans un test ce qu'une version du
moteur pourrait changer. La seconde est plus importante : la prédiction est
mesurée **contre le moteur**, et non contre l'opinion de celui qui a écrit le
test.

## Ce que ce lab touche sur la machine, et ce qu'il rend

C'est le setup le plus intrusif du catalogue, et c'est inhérent au sujet : il
touche le **service** et les **groupes**, pas seulement des conteneurs. Tout ce
qu'il change, il le relève avant dans `/root/.lab-mise-en-marche-state.json`, et
le `cleanup` le remet comme il l'a trouvé :

- le moteur est remis en marche **en premier**, parce que le cycle de validation
  interroge le moteur après le nettoyage et ne peut rien conclure d'un démon
  muet ;
- l'état « activé » est restitué **tel qu'il était**, en gardant la chaîne
  exacte de `systemctl is-enabled` : `static` et `masked` ne se traitent pas
  comme `disabled`, et réactiver aveuglément changerait la machine dans l'autre
  sens ;
- l'appartenance au groupe `docker` est restituée telle quelle. Si le compte n'y
  était pas, il n'y est pas remis : le lab rend ce qu'il a trouvé, pas ce qu'il
  juge souhaitable.

## Ce que l'épreuve ne mesure pas

La construction d'images, les volumes, les ports publiés. Rien de cela n'est au
programme de ce module.
