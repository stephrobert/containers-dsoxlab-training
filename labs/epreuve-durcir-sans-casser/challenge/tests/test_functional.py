"""Tests fonctionnels de l'épreuve de durcissement : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE, et la plus exigeante du parcours : elle a DEUX exigences
critiques, le secret dans l'environnement et le pare-feu désactivé. Les deux
sont des portes ouvertes, et une porte ouverte ne se compense pas par du travail
fait ailleurs.

DEUX MESURES ONT FONDÉ CETTE ÉPREUVE, et elles contredisent un conseil répandu.

LA PREMIÈRE : `NET_BIND_SERVICE` ne sert à rien dans un conteneur Docker. Un
conteneur sans AUCUNE capability écoute parfaitement sur le port 80, parce que
le démon pose `net.ipv4.ip_unprivileged_port_start = 0` : tous les ports y sont
« non privilégiés ». Le conseil « tout retirer sauf NET_BIND_SERVICE » ne retire
donc rien d'utile et n'ajoute rien.

LA SECONDE : la capability qui discrimine ici est `CHOWN`. Mesuré le 2026-11-02,
sur le service de ce lab : sans elle il sort en 77, avec elle seule il démarre,
et `DAC_OVERRIDE` ne suffit pas. Le contrôle ne l'impose pas par son nom, il
mesure que le service tourne avec un jeu RÉDUIT : c'est l'état final qui compte,
et un apprenant qui garderait une capability de plus sans nécessité aurait moins
bien durci.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, ce qui permet de lire le relevé dans `/root` et
les règles du pare-feu.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import lab_host, message

SERVICE = "service-expose"
FOURNISSEUR = "fournisseur-tiers"
IMAGE = "lab-durcir:1.0"
ATELIER = "/opt/lab-durcir"
ETAT = "/root/.lab-durcir-state.json"
VOLUME_UTILE = "dsoxlab-durcir-donnees"
JETABLES = ("dsoxlab-durcir-jetable-1", "dsoxlab-durcir-jetable-2")
TABLE = "lab_durcir"
PORT_FOURNISSEUR = 19443
PORT_PROTEGE = 19444

# Le jeu de capabilities que Docker accorde par défaut. En garder plus que le
# nécessaire est le défaut que l'épreuve corrige ; ce seuil dit « il en reste
# presque autant qu'au départ ».
CAPABILITES_PAR_DEFAUT = 14

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui les
    lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def releve(host) -> dict:
    """Le secret et la donnée tirés au sort par le `run`.

    Ils servent à prouver que le secret est bien ARRIVÉ au service, et que la
    donnée du volume utile est bien celle du départ. Les deux distinguent « c'est
    propre » de « c'est vide ».
    """
    lu = host.run("cat %s", ETAT)
    if lu.rc != 0:
        pytest.fail(message(
            en=f"the lab's own measurement is missing from `{ETAT}`. It is "
               "taken during `dsoxlab run`: replay it.",
            fr=f"la mesure que le lab a prise manque dans `{ETAT}`. Elle est "
               "faite pendant `dsoxlab run` : rejouez-le.",
        ))
    return json.loads(lu.stdout)


def test_le_service_a_perdu_ses_droits_et_repond_encore(host, releve) -> None:
    """Durcir sans casser, et les deux moitiés comptent autant.

    TROIS FAITS. Le jeu de capabilities est réduit, `no-new-privileges` est
    posé, et le service RÉPOND. Le troisième est ce qui distingue cette épreuve
    d'un exercice de suppression : tout retirer est facile, et le service meurt.

    LE CONTRÔLE N'IMPOSE AUCUNE CAPABILITY PAR SON NOM. Il mesure que le jeu est
    réduit et que le service tourne : c'est l'état final qui compte. Un apprenant
    qui trouve un autre chemin pour se passer de `CHOWN`, par exemple en
    préparant les droits autrement, a mieux durci, et l'épreuve ne doit pas le
    punir.
    """
    etat = _inspecte(host, SERVICE)
    hote = etat["HostConfig"]
    retirees = hote.get("CapDrop") or []
    ajoutees = hote.get("CapAdd") or []

    tout_retire = any(c.upper() in {"ALL", "CAP_ALL"} for c in retirees)
    assert tout_retire or len(retirees) >= CAPABILITES_PAR_DEFAUT - 2, message(
        en=f"`{SERVICE}` still carries nearly all the default capabilities.\n"
           f"  dropped: {', '.join(retirees) or '(none)'}\n"
           f"  added  : {', '.join(ajoutees) or '(none)'}\n"
           "Docker grants a set by default, and a service needs almost none of "
           "it. Dropping everything and adding back what is needed is the move "
           "that leaves no doubt.",
        fr=f"`{SERVICE}` porte encore presque toutes les capabilities par "
           "défaut.\n"
           f"  retirées : {', '.join(retirees) or '(aucune)'}\n"
           f"  ajoutées : {', '.join(ajoutees) or '(aucune)'}\n"
           "Docker en accorde un jeu par défaut, et un service n'en a presque "
           "aucun besoin. Tout retirer puis rajouter le nécessaire est le geste "
           "qui ne laisse aucun doute.",
    )
    assert len(ajoutees) <= 2, message(
        en=f"`{SERVICE}` adds back {len(ajoutees)} capabilities: "
           f"{', '.join(ajoutees)}.\n"
           "Only what is necessary is expected, and the service's logs say "
           "which move fails when it is missing.",
        fr=f"`{SERVICE}` rajoute {len(ajoutees)} capabilities : "
           f"{', '.join(ajoutees)}.\n"
           "Seul le nécessaire est attendu, et les journaux du service disent "
           "quel geste échoue quand il manque.",
    )

    options = hote.get("SecurityOpt") or []
    assert any("no-new-privileges" in o for o in options), message(
        en=f"`{SERVICE}` does not carry `no-new-privileges`.\n"
           f"  its security options: {', '.join(options) or '(none)'}\n"
           "Without it, a setuid binary inside the image can still regain what "
           "the capabilities were dropped for.",
        fr=f"`{SERVICE}` ne porte pas `no-new-privileges`.\n"
           f"  ses options de sécurité : {', '.join(options) or '(aucune)'}\n"
           "Sans elle, un binaire setuid de l'image peut regagner ce que le "
           "retrait des capabilities visait à lui ôter.",
    )

    statut = etat["State"]["Status"]
    assert statut == "running", message(
        en=f"`{SERVICE}` is `{statut}`: hardening has killed it.\n"
           f"  exit code: {etat['State']['ExitCode']}\n"
           "Hardening without breaking is the whole test. The service's logs "
           "say which move it could no longer perform.",
        fr=f"`{SERVICE}` est `{statut}` : le durcissement l'a tué.\n"
           f"  code de sortie : {etat['State']['ExitCode']}\n"
           "Durcir sans casser est tout le sujet. Les journaux du service "
           "disent quel geste il n'a plus pu accomplir.",
    )
    recu = _interroge(host, SERVICE)
    assert f"service={releve['secret']}" in recu, message(
        en=f"`{SERVICE}` runs but does not serve the right value.\n"
           f"  what came back: {recu.strip()[:200] or '(nothing)'}",
        fr=f"`{SERVICE}` tourne mais ne sert pas la bonne valeur.\n"
           f"  ce qui revient : {recu.strip()[:200] or '(rien)'}",
    )


def test_la_racine_est_en_lecture_seule_et_les_ecritures_sont_declarees(
    host,
) -> None:
    """Deux faits qui n'ont de sens qu'ensemble.

    Une racine en lecture seule sans chemin d'écriture déclaré donne un service
    qui meurt ; un chemin déclaré sans racine en lecture seule ne protège rien.
    Le contrôle mesure donc les deux, et il les mesure EN FAISANT : une écriture
    hors des chemins déclarés doit être refusée, et une écriture dans un chemin
    déclaré doit passer.

    Lire `ReadonlyRootfs` ne suffirait pas : le drapeau dit l'intention, l'essai
    dit le résultat.
    """
    etat = _inspecte(host, SERVICE)
    assert etat["HostConfig"].get("ReadonlyRootfs"), message(
        en=f"`{SERVICE}` does not have a read-only root filesystem.\n"
           "Anything that gets into the container can then write wherever it "
           "likes, including over the binaries it runs.",
        fr=f"`{SERVICE}` n'a pas sa racine en lecture seule.\n"
           "Tout ce qui entre dans le conteneur peut alors écrire où il veut, "
           "y compris par-dessus les binaires qu'il exécute.",
    )

    refus = host.run(
        "docker exec %s sh -c %s", SERVICE,
        "echo essai > /interdit-par-l-epreuve 2>&1 || echo REFUSE",
    )
    assert "REFUSE" in refus.stdout, message(
        en="writing at the root of the container is not refused.\n"
           f"  what came back: {refus.stdout.strip()[:200] or '(nothing)'}\n"
           "The flag says the intention; the attempt says the result.",
        fr="une écriture à la racine du conteneur n'est pas refusée.\n"
           f"  ce qui revient : {refus.stdout.strip()[:200] or '(rien)'}\n"
           "Le drapeau dit l'intention, l'essai dit le résultat.",
    )

    # ET LE SERVICE PEUT ÉCRIRE LÀ OÙ IL DOIT : il l'a déjà prouvé en démarrant,
    # puisqu'il écrit son jeton de travail avant de servir. On relit ce fichier
    # dans le conteneur, ce qui mesure le chemin déclaré sans le supposer.
    travail = host.run(
        "docker container inspect %s --format %s",
        SERVICE,
        "{{range .Config.Env}}{{println .}}{{end}}",
    )
    chemin = "/travail"
    for ligne in travail.stdout.splitlines():
        if ligne.startswith("TRAVAIL="):
            chemin = ligne.split("=", 1)[1].strip() or chemin
    lu = host.run("docker exec %s cat %s", SERVICE, f"{chemin}/jeton-en-cours")
    assert lu.rc == 0 and lu.stdout.strip(), message(
        en=f"the service cannot write into its declared working directory "
           f"(`{chemin}`).\n"
           "A read-only root with no declared writable path gives a service "
           "that dies: the two go together.",
        fr=f"le service ne peut pas écrire dans son répertoire de travail "
           f"déclaré (`{chemin}`).\n"
           "Une racine en lecture seule sans chemin d'écriture déclaré donne un "
           "service qui meurt : les deux vont ensemble.",
    )


def test_le_secret_n_est_ni_dans_l_environnement_ni_dans_l_image(
    host, releve
) -> None:
    """PREMIÈRE EXIGENCE CRITIQUE, et elle a deux faces.

    Le secret ne doit plus être lisible dans l'environnement du conteneur ni
    dans l'image. ET il doit être arrivé au service : retirer une variable sans
    la remplacer donne un service propre et muet, ou qui sert une valeur par
    défaut.

    Le contrôle compare donc la valeur servie à celle que le lab a tirée au
    sort : elle ne peut être juste que si le secret est bien arrivé.
    """
    secret = releve["secret"]
    assert secret, message(
        en="the lab's own measurement carries no secret. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte pas de secret. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )

    env = host.run(
        "docker container inspect %s --format %s",
        SERVICE,
        "{{range .Config.Env}}{{println .}}{{end}}",
    )
    fautives = [l.strip() for l in env.stdout.splitlines() if secret in l]
    assert not fautives, message(
        en=f"the secret is readable in `{SERVICE}`'s environment:\n"
           + "\n".join(f"  {l}" for l in fautives) + "\n"
           "An environment variable is read by `docker inspect` and by anyone "
           "who can talk to the daemon. No total makes up for it.",
        fr=f"le secret se lit dans l'environnement de `{SERVICE}` :\n"
           + "\n".join(f"  {l}" for l in fautives) + "\n"
           "Une variable d'environnement se lit par `docker inspect` et par "
           "quiconque parle au démon. Aucun total ne le compense.",
    )

    dans_image = host.run("docker save %s | grep -a -c %s || true", IMAGE, secret)
    compte = dans_image.stdout.strip() or "0"
    assert compte == "0", message(
        en=f"the secret is present in the image's layers ({compte} "
           "occurrence(s)).\n"
           "Moving a secret from the environment into the image moves it from "
           "readable to published.",
        fr=f"le secret est présent dans les couches de l'image ({compte} "
           "occurrence(s)).\n"
           "Déplacer un secret de l'environnement vers l'image, c'est le faire "
           "passer de lisible à publié.",
    )

    recu = _interroge(host, SERVICE)
    assert f"service={secret}" in recu, message(
        en=f"the secret no longer reaches the service.\n"
           f"  what it serves: {recu.strip()[:200] or '(nothing)'}\n"
           "Removing a secret without replacing it is not a fix: the service is "
           "clean and wrong.",
        fr=f"le secret n'arrive plus au service.\n"
           f"  ce qu'il sert : {recu.strip()[:200] or '(rien)'}\n"
           "Retirer un secret sans le remplacer n'est pas une correction : le "
           "service est propre et faux.",
    )


def test_le_flux_aboutit_et_le_pare_feu_reste_actif(host, releve) -> None:
    """SECONDE EXIGENCE CRITIQUE : le pare-feu désactivé.

    C'est la fausse correction la plus tentante de toute l'épreuve. Le flux ne
    passe pas, le pare-feu bloque, donc on retire le pare-feu : le symptôme
    disparaît en une commande, et la machine est nue.

    TROIS FAITS SONT MESURÉS ENSEMBLE. Le flux aboutit, la table du pare-feu
    existe toujours, et sa règle de protection est intacte. Le troisième est le
    plus fin : une correction qui vide la chaîne lève le blocage ET la
    protection, ce qui ressemble à un travail fait.
    """
    table = host.run("nft list table inet %s", TABLE)
    assert table.rc == 0, message(
        en=f"the `{TABLE}` firewall table no longer exists.\n"
           "Removing the firewall makes the symptom vanish in one command and "
           "leaves the machine bare. No total makes up for that.",
        fr=f"la table de pare-feu `{TABLE}` n'existe plus.\n"
           "Retirer le pare-feu fait disparaître le symptôme en une commande et "
           "laisse la machine nue. Aucun total ne le compense.",
    )
    assert "protection a conserver" in table.stdout, message(
        en=f"the protection rule has disappeared from the `{TABLE}` table.\n"
           "A fix that flushes the chain lifts the block AND the protection, "
           "which looks like a job done and is a door left open.",
        fr=f"la règle de protection a disparu de la table `{TABLE}`.\n"
           "Une correction qui vide la chaîne lève le blocage ET la protection, "
           "ce qui ressemble à un travail fait et laisse une porte ouverte.",
    )
    # ET LA PROTECTION PROTÈGE ENCORE : lire la règle ne dit pas qu'elle agit.
    protege = host.run("nc -w 3 %s %s", "127.0.0.1", str(PORT_PROTEGE))
    assert not protege.stdout.strip(), message(
        en=f"port {PORT_PROTEGE} is no longer filtered, although its rule is "
           "still written.\n"
           "A rule placed after an accept that matches first no longer does "
           "anything: in a chain, order decides.",
        fr=f"le port {PORT_PROTEGE} n'est plus filtré, alors que sa règle est "
           "toujours écrite.\n"
           "Une règle placée après une acceptation qui matche d'abord ne fait "
           "plus rien : dans une chaîne, l'ordre décide.",
    )

    recu = host.run("nc -w 3 %s %s", "127.0.0.1", str(PORT_FOURNISSEUR))
    attendu = f"fournisseur={releve['donnee']}"
    assert attendu in recu.stdout, message(
        en=f"the flow to the provider still does not get through on "
           f"127.0.0.1:{PORT_FOURNISSEUR}.\n"
           f"  what came back: {recu.stdout.strip()[:200] or '(nothing)'}\n"
           f"  expected      : {attendu}\n"
           "The firewall can be corrected without being disabled: in a chain, "
           "a rule that accepts can take precedence over one that blocks, "
           "depending on their order.",
        fr=f"le flux vers le fournisseur ne passe toujours pas sur "
           f"127.0.0.1:{PORT_FOURNISSEUR}.\n"
           f"  ce qui revient : {recu.stdout.strip()[:200] or '(rien)'}\n"
           f"  attendu        : {attendu}\n"
           "Le pare-feu se corrige sans être désactivé : dans une chaîne, une "
           "règle qui autorise peut primer sur une règle qui bloque, selon leur "
           "ordre.",
    )


def test_le_volume_utile_est_servi_et_les_jetables_sont_retires(
    host, releve
) -> None:
    """Distinguer ce qu'on garde de ce qu'on jette, et le prouver par la donnée.

    Le durcissement passe par une recréation du conteneur, et c'est là qu'un
    volume s'oublie. Trois volumes portent le nom du lab : un seul compte, et
    l'énoncé dit lequel.

    LE CONTRÔLE LIT LA DONNÉE SERVIE, et non la seule existence du volume : un
    volume remonté vide porte le bon nom et ne vaut rien. Et il la lit dans la
    RÉPONSE du service, ce qui prouve du même coup que le montage est au bon
    endroit.
    """
    attendue = releve["donnee"]
    assert attendue, message(
        en="the lab's own measurement carries no reference value. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte pas la donnée de référence. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )

    existe = host.run("docker volume inspect %s", VOLUME_UTILE)
    assert existe.rc == 0, message(
        en=f"the `{VOLUME_UTILE}` volume no longer exists.",
        fr=f"le volume `{VOLUME_UTILE}` n'existe plus.",
    )
    recu = _interroge(host, SERVICE)
    assert f"donnee={attendue}" in recu, message(
        en=f"the service does not serve the useful volume's value.\n"
           f"  what came back: {recu.strip()[:200] or '(nothing)'}\n"
           f"  expected      : donnee={attendue}\n"
           "Either the volume is not mounted back, or it is mounted somewhere "
           "else: a volume remounted empty carries the right name and is worth "
           "nothing.",
        fr=f"le service ne sert pas la donnée du volume utile.\n"
           f"  ce qui revient : {recu.strip()[:200] or '(rien)'}\n"
           f"  attendu        : donnee={attendue}\n"
           "Soit le volume n'est pas remonté, soit il l'est ailleurs : un "
           "volume remonté vide porte le bon nom et ne vaut rien.",
    )

    liste = host.run("docker volume ls -q")
    presents = {v.strip() for v in liste.stdout.splitlines() if v.strip()}
    restants = sorted(set(JETABLES) & presents)
    assert not restants, message(
        en=f"the disposable volumes are still there:\n"
           + "\n".join(f"  {v}" for v in restants) + "\n"
           "The brief names which volume counts. Keeping everything is not "
           "caution, it is leaving the next person to guess.",
        fr=f"les volumes jetables sont encore là :\n"
           + "\n".join(f"  {v}" for v in restants) + "\n"
           "L'énoncé nomme le volume qui compte. Tout garder n'est pas de la "
           "prudence, c'est laisser le suivant deviner.",
    )


def _inspecte(host, nom: str) -> dict:
    """L'inspection complète d'un conteneur, ou un échec qui nomme l'absence."""
    res = host.run("docker container inspect %s", nom)
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. The brief names it, and the "
               "checks look for it by name: if you recreated it, it has to "
               "carry the same name.",
            fr=f"le conteneur `{nom}` n'existe pas. L'énoncé le nomme, et les "
               "contrôles le cherchent nommément : si vous l'avez recréé, il "
               "doit porter le même nom.",
        ))
    return json.loads(res.stdout)[0]


def _interroge(host, nom: str) -> str:
    """Ce que le service répond, lu DANS son conteneur.

    Dans son conteneur, parce que ce lab ne publie aucun port pour le service :
    son sujet est le durcissement, pas le réseau. La réponse est lue, jamais la
    seule connexion : le proxy de Docker accepte dès le `run`.
    """
    dernier = ""
    for _ in range(8):
        res = host.run("docker exec %s nc -w 3 127.0.0.1 80", nom)
        dernier = res.stdout
        if "service=" in dernier:
            return dernier
    return dernier
