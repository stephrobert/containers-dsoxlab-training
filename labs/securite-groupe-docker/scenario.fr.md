# Scénario

Un compte d'audit temporaire, `dsoxlab-auditor`, n'a plus besoin de son accès au
démon Docker. Cet accès équivaut à root sur cette machine, puisqu'il donne
l'écriture sur le socket du moteur.

## Mission

`dsoxlab-auditor` existe toujours, mais **ne peut plus joindre le démon**.

Deux contrôles le mesurent, et le second est le plus exigeant : il ne lit pas une
ligne de configuration, il tente un vrai appel au moteur sous ce compte. Un
`docker ps` doit y échouer sur un refus de permission.

La distinction compte, parce que **l'appartenance au groupe n'est qu'une des
voies** vers le socket. Retirer le compte du groupe `docker` sans toucher au
reste suffit ici ; mais si une autre voie subsistait, une ACL posée sur le
fichier du socket par exemple, le premier contrôle serait satisfait et le compte
garderait son privilège. C'est l'accès qui est mesuré, pas sa déclaration.

Si vous employez des ACL, sachez que `ls -l` affiche encore le `+` après un
`setfacl -x`, le masque restant en place : seul `getfacl` dit ce qui subsiste.

## Deux interdictions

- **Conservez le compte.** Le supprimer retire bien son accès, en supprimant ce
  que l'exercice demande de garder : le compte d'audit reste, seul son privilège
  part.
- **Ne modifiez pas vos propres accès.** Vider le groupe `docker` de tous ses
  membres retirerait l'accès du compte d'audit, et avec lui celui dont le travail
  a besoin.

Les deux sont vérifiées avant les mesures, et leur message nomme celle qui a été
franchie.
