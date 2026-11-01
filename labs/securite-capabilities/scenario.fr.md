# Un service trop privilégié

Un petit worker a été déployé avec les capabilities root par défaut de Docker.
Son seul privilège nécessaire est l'écoute sur un port privilégié. Changer les
propriétaires ne fait pas partie de son travail.

Dans `/opt/dsoxlab-securite-capabilities`, limitez le `worker` actif à
NET_BIND_SERVICE uniquement. Conservez le projet `dsoxlab-securite-capabilities`,
son label de lab et `/proof`. Le contrôle observe la configuration Docker et le
masque effectif de PID 1, puis tente un changement de propriétaire inoffensif.

Seul ce projet jetable est concerné. Ne modifiez pas le démon, n'utilisez pas le
mode privileged et ne touchez aucun autre conteneur.
