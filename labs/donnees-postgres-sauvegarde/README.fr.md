# Sauvegarde et restauration PostgreSQL

Le test fonctionnel vérifie une véritable sauvegarde PostgreSQL au format
personnalisé : il la restaure dans une base temporaire isolée et compare les
lignes réelles à celles de la source et de la base demandée. La base d'essai
est supprimée même si une vérification échoue.

Le nettoyage supprime uniquement les bases portant le marqueur aléatoire de
cette session et retire le répertoire de sauvegarde du lab.
