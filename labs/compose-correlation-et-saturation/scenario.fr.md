# Quel composant est saturé ?

Une API de devis associe la passerelle et le calculateur CPU fournis. Ses traces
ne permettent pas de reconstituer une requête et le déploiement expose des
en-têtes. Configurez `/opt/dsoxlab-compose-correlation-et-saturation`,
sans réécrire les applications.

Mesurez une charge métier bornée, attribuez la saturation grâce aux compteurs
cgroup effectifs et conservez des identifiants de requête frais de bout en bout.
Ne conservez jamais Authorization ni le témoin de test dans les journaux.

Consultez [le contrat numéroté](challenge/README.fr.md) et la revue humaine séparée.
