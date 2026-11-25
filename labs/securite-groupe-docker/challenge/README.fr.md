# Un compte d'audit qui n'a plus besoin du moteur

## La situation

Sur `docker.lab`, le compte d'audit temporaire `dsoxlab-auditor` peut encore
joindre le démon Docker. Cet accès équivaut à root sur la machine, et sa mission
est terminée.

## Mission

`dsoxlab-auditor` existe toujours, mais **ne peut plus joindre le démon**. Un
`docker ps` lancé sous ce compte doit échouer sur un refus de permission.

Deux interdictions :

- **Conservez le compte**, et le reste de ses droits.
- **Ne modifiez pas vos propres accès** : le groupe `docker` garde ses autres
  membres.

## Ce qui est noté

1. Le compte n'est plus membre du groupe `docker`.
2. Un vrai appel au moteur, sous ce compte, est refusé. L'appartenance au groupe
   n'est qu'une voie vers le socket : une ACL posée sur son fichier laisserait le
   privilège. `getfacl` montre ce qui subsiste ; `ls -l` affiche encore le `+`
   après un `setfacl -x`, car le masque reste en place.

Franchir une interdiction fait échouer les deux contrôles, et le message la
nomme.
