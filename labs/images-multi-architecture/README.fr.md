# Un index d'images n'est pas un résultat d'exécution

Un index multi-plateforme associe une plateforme au digest d'un manifeste.
Chaque manifeste désigne une configuration et des couches. Modifier la
métadonnée de plateforme ne traduit pas les instructions d'un exécutable.

Trois opérations sont distinctes : compiler pour une architecture, assembler
son image et exécuter cette image. Par exemple, `GOOS` et `GOARCH` choisissent
la plateforme produite par Go ; `CGO_ENABLED=0` permet un binaire Linux autonome
pour une image scratch. `--platform` choisit les métadonnées Docker et, lors
du pull d'un index, le manifeste approprié.

Dans une VM Linux AMD64, un exécutable ARM64 demande un interpréteur tel que
QEMU enregistré avec binfmt, ou du matériel ARM64 natif. L'interpréteur doit
rester dans la VM de lab, pas sur le poste de l'apprenant. Une exécution sous
émulation prouve le comportement fonctionnel de cet environnement seulement.

Une preuve acceptable comporte le digest d'index, les deux manifestes, des
contrôles runtime positifs et négatifs et la distinction natif/émulé.
