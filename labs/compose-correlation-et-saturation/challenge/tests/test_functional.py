"""Quatre verdicts sur une seule mesure.

Pourquoi quatre contrôles là où il n'y en avait qu'un
----------------------------------------------------

Le fichier précédent portait **un** `def test_` dont la seule assertion était
« la sonde sort en 0 ». Toute la mesure vivait dans `probe.py`, avec une
trentaine d'assertions enchaînées : la première qui tombait masquait les autres,
et l'apprenant recevait un bloc de stderr tronqué à 900 caractères pour tout
diagnostic, sur une charge de deux minutes.

CE LAB NE SE DÉCOUPE PAS EN REJOUANT LA CHARGE. Elle démarre deux composants,
attend leur disponibilité, envoie seize requêtes concurrentes et relève les
cgroups avant et après. La rejouer quatre fois quadruplerait un cycle déjà long
pour mesurer quatre fois la même chose.

Le découpage juste est donc l'autre : **la mesure est une, les verdicts sont
plusieurs**. La sonde mesure et rend ses faits ; ce fichier les juge, une
famille d'exigences par contrôle. C'est le premier lab du catalogue où le
découpage prend cette forme, et c'est sa charge qui l'impose.

Les quatre familles, que le scénario énonce :

1. les quotas CPU sont **durs** et différenciés, pas des poids relatifs ;
2. chaque requête métier est **corrélée de bout en bout**, sans trou ni doublon ;
3. la saturation mesurée est **attribuable** au calculateur ;
4. les en-têtes sensibles ne sortent **jamais** dans les journaux.

LA QUATRIÈME PORTE SA PROPRE PREUVE DE REFUS, et c'est l'idée la plus solide du
lab d'origine, conservée et rendue explicite. Un critère de journaux sûrs qui ne
voit passer qu'une stack bien configurée n'est jamais éprouvé : il pourrait être
incapable de refuser sans que personne le sache. La sonde dérive donc de la
configuration de l'apprenant une **variante de surface** (mêmes quotas, même
corrélation, journaux du calculateur laissés bavards), et le contrôle applique
son propre critère aux deux relevés : vide sur la stack de l'apprenant, non vide
sur la variante. Le critère prouve ainsi qu'il sait dire non.

Ce qui vit en garde-fou plutôt qu'en contrôle : l'image épinglée, l'absence de
privilèges, l'absence de capacités ajoutées, le label du lab et le namespace
cgroup privé. Ces cinq faits sont posés par le `compose.yaml` fourni, que
l'apprenant n'a pas à produire. Les franchir est une faute qui doit se dire, mais
les mesurer comme un contrôle accorderait des points pour un travail que
personne n'a fait.
"""

import json

import pytest

from conftest import lab_host, message

SONDE = __file__.replace("test_functional.py", "probe.py")
PRIX_UNITAIRE = 125


@pytest.fixture(scope="module")
def mesure():
    """Un seul passage de la sonde pour les quatre contrôles.

    `scope="module"` est le point d'équilibre de ce lab : chaque contrôle garde
    son verdict et son message, sans que la charge se rejoue. Si la collecte
    échoue, les quatre contrôles tombent en erreur avec la même cause nommée,
    ce qui est exactement ce qu'il faut dire : rien n'a pu être mesuré.
    """
    with open(SONDE, encoding="utf-8") as source:
        script = source.read()
    resultat = lab_host("docker.lab").run(
        "env DSOXLAB_LANG=%s timeout 150 python3 -c %s",
        message(en="en", fr="fr"), script,
    )
    assert resultat.rc == 0, message(
        en="The measurement could not be taken: " + resultat.stderr.strip()[-700:],
        fr="La mesure n'a pas pu être prise : " + resultat.stderr.strip()[-700:],
    )
    return json.loads(resultat.stdout)


@pytest.fixture(scope="module")
def releve(mesure):
    """Le relevé de la stack de l'apprenant."""
    return mesure["apprenant"]


@pytest.fixture(scope="module")
def variante(mesure):
    """Le relevé de la variante de surface, pris dans le même passage."""
    return mesure["variante"]


def _socle_intact(releve) -> None:
    """Le socle fourni n'a pas été dégradé.

    GARDE-FOU ET NON EXIGENCE : ces cinq faits viennent du `compose.yaml` du
    lab. Un apprenant qui ajoute `privileged: true` pour « que ça passe »
    obtiendrait des cgroups qui ne contraignent plus rien, et il doit l'entendre.
    """
    for role, faits in releve["faits"].items():
        assert faits["en_cours"], message(
            en=f"Component {role} is not running.",
            fr=f"Le composant {role} ne tourne pas.",
        )
        assert faits["image_epinglee"], message(
            en=f"Component {role} no longer runs the pinned image supplied by the "
               "lab: the measurement would describe something else.",
            fr=f"Le composant {role} ne tourne plus l'image épinglée fournie par "
               "le lab : la mesure décrirait autre chose.",
        )
        assert not faits["privilegie"] and not faits["cap_add"], message(
            en=f"Component {role} was granted privileges or capabilities "
               f"({faits['cap_add']}): a privileged container escapes the very "
               "limits this lab measures.",
            fr=f"Le composant {role} a reçu des privilèges ou des capacités "
               f"({faits['cap_add']}) : un conteneur privilégié échappe aux "
               "limites mêmes que ce lab mesure.",
        )
        assert faits["label"] == "compose-correlation-et-saturation", message(
            en=f"Component {role} lost its dsoxlab.lab label, which is how the "
               "cleanup finds it.",
            fr=f"Le composant {role} a perdu son label dsoxlab.lab, par lequel le "
               "nettoyage le retrouve.",
        )
        assert faits["cgroupns"] == "private", message(
            en=f"Component {role} shares the host cgroup namespace, so "
               "/sys/fs/cgroup inside it describes the host, not the container.",
            fr=f"Le composant {role} partage le namespace cgroup de l'hôte, donc "
               "/sys/fs/cgroup y décrit l'hôte, pas le conteneur.",
        )


def _journaux_non_surs(releve) -> list[str]:
    """Les fautes de confidentialité d'un relevé, et la liste est le verdict.

    Fonction et non assertion, parce qu'elle est appliquée DEUX fois : à la
    stack de l'apprenant, où elle doit être vide, et à la variante de surface,
    où elle ne doit pas l'être.
    """
    fautes = []
    for role, journal in releve["journaux"].items():
        if journal["temoin_present"]:
            fautes.append(f"{role}: la valeur du jeton apparaît en clair")
        if journal["autorisation_presente"]:
            fautes.append(f"{role}: le nom de l'en-tête Authorization apparaît")
    return fautes


def test_les_quotas_cpu_sont_durs_et_differencies(releve):
    """Un quota, pas un poids, et pas le même pour les deux composants.

    `cpu.max` à `max` signifie qu'aucun plafond n'existe : un poids relatif
    (`cpu.weight`) ne se voit que lorsque la machine est chargée, et ne garantit
    rien. Ce lab mesure un étranglement ; sans plafond, il n'y en a pas.
    """
    _socle_intact(releve)
    plafonds = {}
    for role, faits in releve["faits"].items():
        assert faits["quota"] != "max", message(
            en=f"Component {role} has no CPU ceiling (cpu.max is 'max'). Relative "
               "shares only show under contention and guarantee nothing: declare "
               "a hard quota with cpus.",
            fr=f"Le composant {role} n'a aucun plafond CPU (cpu.max vaut « max »). "
               "Un poids relatif ne se voit qu'en contention et ne garantit "
               "rien : déclarez un quota strict avec cpus.",
        )
        plafonds[role] = int(faits["quota"]) / faits["period"]
    assert plafonds == {"gateway": 1.0, "worker": 0.25}, message(
        en=f"Measured ceilings are {plafonds}, expected one CPU for the gateway "
           "and a quarter CPU for the calculator: the calculator is the component "
           "to isolate, and the gateway must stay able to answer.",
        fr=f"Les plafonds mesurés valent {plafonds} au lieu d'un CPU pour la "
           "passerelle et un quart de CPU pour le calculateur : c'est le "
           "calculateur qu'il faut isoler, et la passerelle doit rester capable "
           "de répondre.",
    )


def test_chaque_requete_metier_est_correlee_de_bout_en_bout(releve):
    """Seize identités fraîches, retrouvées une fois et une seule, des deux côtés.

    Trois défauts distincts se cachent derrière « la corrélation ne marche
    pas » : la trace manque, la trace est dupliquée, la trace est fausse. Ils
    appellent trois gestes différents, donc ils se disent séparément.
    """
    _socle_intact(releve)
    identites, quantites = releve["identites"], releve["quantites"]

    for index, (statut, corps) in enumerate(releve["reponses"]):
        attendu = {
            "request_id": identites[index],
            "quantity": quantites[index],
            "total_cents": quantites[index] * PRIX_UNITAIRE,
        }
        assert statut == 200, message(
            en=f"Business request {index} answered HTTP {statut} instead of 200: "
               f"{corps}",
            fr=f"La requête métier {index} a répondu HTTP {statut} au lieu de "
               f"200 : {corps}",
        )
        assert corps == attendu, message(
            en=f"Business answer {index} is {corps}, expected {attendu}: either "
               "the price is wrong or the request id is not carried back.",
            fr=f"La réponse métier {index} vaut {corps} au lieu de {attendu} : "
               "soit le prix est faux, soit l'identifiant de requête n'est pas "
               "rendu.",
        )

    assert releve["invalide"] == [400, {"error": "invalid_quote"}], message(
        en=f"A quantity of zero got {releve['invalide']} instead of 400 "
           "invalid_quote: a gateway that prices nothing at all prices anything.",
        fr=f"Une quantité nulle a obtenu {releve['invalide']} au lieu de 400 "
           "invalid_quote : une passerelle qui tarife le vide tarife n'importe "
           "quoi.",
    )

    for role, journal in releve["journaux"].items():
        for index, traces in enumerate(journal["traces"]):
            attendu = {
                "component": role,
                "event": "quote_finished",
                "request_id": identites[index],
                "quantity": quantites[index],
                "total_cents": quantites[index] * PRIX_UNITAIRE,
            }
            assert traces, message(
                en=f"Component {role} logged no JSON trace for request {index}: "
                   "correlation is end to end, and one silent component breaks "
                   "the chain.",
                fr=f"Le composant {role} n'a journalisé aucune trace JSON pour la "
                   f"requête {index} : la corrélation est de bout en bout, et un "
                   "composant muet rompt la chaîne.",
            )
            assert len(traces) == 1, message(
                en=f"Component {role} logged {len(traces)} traces for request "
                   f"{index}: a duplicated identifier makes a trace uncountable.",
                fr=f"Le composant {role} a journalisé {len(traces)} traces pour la "
                   f"requête {index} : un identifiant dupliqué rend une trace "
                   "incomptable.",
            )
            assert traces[0] == attendu, message(
                en=f"Component {role} logged {traces[0]} for request {index}, "
                   f"expected {attendu}.",
                fr=f"Le composant {role} a journalisé {traces[0]} pour la requête "
                   f"{index} au lieu de {attendu}.",
            )


def test_la_saturation_est_attribuee_au_calculateur(releve):
    """L'étranglement a eu lieu, et sur le bon composant.

    « Le service est lent » n'est pas un diagnostic. Le compteur
    `nr_throttled` du cgroup dit que le noyau a suspendu le processus parce que
    son quota était épuisé : c'est la différence entre constater et attribuer.
    """
    _socle_intact(releve)
    worker, gateway = releve["delta"]["worker"], releve["delta"]["gateway"]
    plancher = releve["count"] * 100000

    assert worker["usage_usec"] >= plancher, message(
        en=f"The calculator consumed {worker['usage_usec']} us of CPU, below the "
           f"{plancher} us the bounded load implies: it is not doing the work, so "
           "there is nothing to attribute.",
        fr=f"Le calculateur a consommé {worker['usage_usec']} us de CPU, sous les "
           f"{plancher} us que la charge bornée implique : il ne fait pas le "
           "travail, donc il n'y a rien à attribuer.",
    )
    assert worker["nr_throttled"] > 0 and worker["throttled_usec"] > 0, message(
        en=f"The calculator was never throttled (nr_throttled="
           f"{worker['nr_throttled']}, throttled_usec={worker['throttled_usec']}). "
           "Slowness is not a diagnosis: the cgroup counter is what names the "
           "quota as the cause.",
        fr=f"Le calculateur n'a jamais été étranglé (nr_throttled="
           f"{worker['nr_throttled']}, throttled_usec={worker['throttled_usec']}). "
           "La lenteur n'est pas un diagnostic : c'est le compteur du cgroup qui "
           "désigne le quota comme cause.",
    )
    assert worker["usage_usec"] > gateway["usage_usec"] * 2, message(
        en=f"The calculator used {worker['usage_usec']} us against the gateway's "
           f"{gateway['usage_usec']} us: the load is not attributable to the "
           "calculator, so throttling it would not relieve anything.",
        fr=f"Le calculateur a utilisé {worker['usage_usec']} us contre "
           f"{gateway['usage_usec']} us pour la passerelle : la charge n'est pas "
           "attribuable au calculateur, donc l'étrangler ne soulagerait rien.",
    )


def test_les_en_tetes_sensibles_ne_sortent_jamais_des_journaux(releve, variante):
    """Le critère, et la preuve que ce critère sait refuser.

    Appliqué deux fois : vide sur la stack de l'apprenant, non vide sur une
    variante de surface dérivée de SA configuration, aux mêmes quotas et à la
    même corrélation, dont seuls les journaux du calculateur sont laissés
    bavards. Un critère qui ne voit passer que du conforme n'a jamais été
    éprouvé, et pourrait être incapable de dire non.
    """
    _socle_intact(releve)
    fautes = _journaux_non_surs(releve)
    assert not fautes, message(
        en="Sensitive headers reached the component logs: " + " ; ".join(fautes)
        + ". A JSON trace carries business values and a fresh identifier, never "
          "the credential that authorized the call.",
        fr="Des en-têtes sensibles sont arrivés dans les journaux des composants : "
        + " ; ".join(fautes) + ". Une trace JSON porte des valeurs métier et un "
          "identifiant frais, jamais l'identifiant qui a autorisé l'appel.",
    )

    assert _journaux_non_surs(variante), message(
        en="A deliberately unsafe variant of your own stack, with the "
           "calculator's logs left verbose, passed this very check. Not your "
           "fault: the check cannot refuse, and a check that cannot refuse "
           "measures nothing. Report it.",
        fr="Une variante volontairement dangereuse de votre propre stack, dont les "
           "journaux du calculateur sont laissés bavards, a passé ce contrôle. Ce "
           "n'est pas votre faute : le contrôle ne sait pas refuser, et un "
           "contrôle qui ne sait pas refuser ne mesure rien. Signalez-le.",
    )
