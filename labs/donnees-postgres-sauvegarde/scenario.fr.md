# Une sauvegarde ne vaut qu'après restauration

Une base PostgreSQL source contient trois lignes de commandes. La base de
restauration et le fichier de sauvegarde n'existent pas. Le compte local
`postgres` est disponible. Les noms uniques des bases, le marqueur et le
répertoire de sauvegarde accessible en écriture figurent dans
`/opt/lab-postgres-sauvegarde/state.env` ; les lignes attendues sont dans
`state.json`.

## Mission

Créez une sauvegarde PostgreSQL au format personnalisé dans
`/opt/lab-postgres-sauvegarde/backup/orders.dump`. Restaurez-la dans la base
`RESTORED_DB` indiquée dans `state.env`, sans modifier la source. Ajoutez à la
base restaurée le commentaire `OWNERSHIP` exact afin que le nettoyage identifie
la ressource créée pour cette session.

La simple présence d'un fichier ne prouve rien : le test fonctionnel restaure
la sauvegarde dans une base temporaire distincte et compare ses lignes à la
source active et à la base de restauration demandée. La base d'essai est ensuite
supprimée.
