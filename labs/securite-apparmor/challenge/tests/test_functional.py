"""Un profil AppArmor dédié, en mode enforce, et qui refuse le bon chemin.

Pourquoi trois contrôles là où il n'y en avait qu'un
---------------------------------------------------

Le fichier précédent portait **un** `def test_` et six assertions enchaînées. Il
mesurait les trois bonnes choses, et le défaut était la forme : la première
assertion qui tombait masquait les cinq suivantes, et son message tenait en trois
mots, « Un service actif requis ».

Les trois contrôles mesurent trois choses indépendantes :

1. le profil **déclaré** sur le conteneur ;
2. le mode que le **noyau applique** à PID 1, qui doit être `enforce` ;
3. ce que le profil **refuse et laisse passer**, éprouvé par deux lectures.

1 et 2 ne sont pas redondants, et la différence est le cœur du sujet : un profil
chargé en `complain` est attaché, visible, et n'empêche rien. Il journalise.
`/proc/1/attr/current` dit lequel des deux modes s'applique, et c'est le seul
endroit qui le dise.

Le troisième ne lit aucune configuration, il essaie deux lectures. Les deux
ensemble font la mesure : refuser le fichier privé prouve que le profil mord,
laisser passer le fichier public prouve qu'il ne mord pas trop. Un profil qui
refuserait tout satisferait la première moitié et casserait le service.

LE PIÈGE QUE LE TROISIÈME CONTRÔLE DÉSAMORCE. Refuser une lecture est aussi ce
qu'un `chmod` obtient, sans AppArmor et sans rien comprendre au sujet. Le mode du
fichier privé est donc vérifié : il doit rester lisible par tous. Un refus doit
venir du profil, pas des droits.
"""

import json

import pytest

from conftest import lab_host, message

LAB = "securite-apparmor"
PROJET = f"dsoxlab-{LAB}"
PROFIL = f"dsoxlab-{LAB}"
PUBLIC = "/lab/public.txt"
PRIVE = "/lab/private.txt"
MODE_ATTENDU = "444"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> tuple[str, dict]:
    """Le conteneur du service, ou un échec qui dit quoi faire.

    Garde-fou de mesure, non exigence : sans un service unique et étiqueté,
    aucun des trois contrôles ne peut observer quoi que ce soit.
    """
    trouve = host.run(
        "docker ps -q --filter label=com.docker.compose.project=%s "
        "--filter label=com.docker.compose.service=worker",
        PROJET,
    )
    ids = trouve.stdout.split()
    assert trouve.rc == 0 and len(ids) == 1, message(
        en=(
            f"Exactly one running `worker` service is required in project "
            f"{PROJET}, found {len(ids)}. Bring the project back up under that "
            "exact name before attaching the profile."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"{PROJET}, {len(ids)} trouvé(s). Relancez le projet sous ce nom "
            "exact avant d'attacher le profil."
        ),
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker : le nettoyage ne retire que ce qui le porte.",
    )
    return cid, info


def test_le_profil_dedie_est_declare_sur_le_conteneur(host):
    """Ce qui a été demandé à Docker."""
    _cid, info = _worker(host)
    attache = info.get("AppArmorProfile") or ""

    assert attache == PROFIL, message(
        en=(
            f"The worker carries the profile « {attache or '(none)'} » instead of "
            f"« {PROFIL} ». A dedicated name is what makes the profile auditable: "
            "the engine's default one applies to everything and proves nothing "
            "about this service."
        ),
        fr=(
            f"Le worker porte le profil « {attache or '(aucun)'} » au lieu de "
            f"« {PROFIL} ». Un nom dédié est ce qui rend le profil auditable : "
            "celui du moteur par défaut s'applique à tout et ne prouve rien sur "
            "ce service."
        ),
    )


def test_le_noyau_applique_le_profil_en_mode_enforce(host):
    """Ce que le noyau applique, qui est la seule vérité.

    Un profil chargé en `complain` est attaché, visible dans l'inspection, et
    n'empêche rien : il journalise. C'est `/proc/1/attr/current` qui dit lequel
    des deux modes s'applique.
    """
    cid, _info = _worker(host)

    lu = host.run("docker exec %s cat /proc/1/attr/current", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read /proc/1/attr/current inside the worker: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"/proc/1/attr/current est illisible dans le worker : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    actif = lu.stdout.strip()
    assert actif == f"{PROFIL} (enforce)", message(
        en=(
            f"PID 1 reports « {actif or '(nothing)'} » instead of "
            f"« {PROFIL} (enforce) ».\n"
            "A profile in `complain` mode is attached and refuses nothing: it "
            "only writes to the log. Loading it is not enough, it must be "
            "enforced."
        ),
        fr=(
            f"PID 1 annonce « {actif or '(rien)'} » au lieu de "
            f"« {PROFIL} (enforce) ».\n"
            "Un profil en mode `complain` est attaché et ne refuse rien : il "
            "écrit seulement dans le journal. Le charger ne suffit pas, il faut "
            "qu'il soit appliqué."
        ),
    )


def test_le_profil_refuse_la_lecture_privee_sans_casser_la_publique(host):
    """Ce que le profil fait réellement, éprouvé par deux lectures.

    Les deux contrôles précédents lisent une configuration ; celui-ci essaie.
    Les deux lectures ensemble font la mesure, et le mode du fichier privé est
    vérifié au passage : un refus doit venir du profil, pas d'un `chmod`.
    """
    cid, _info = _worker(host)

    public = host.run("docker exec %s cat %s", cid, PUBLIC)
    assert public.rc == 0 and public.stdout == "public", message(
        en=(
            f"The public read of {PUBLIC} no longer works: "
            f"{(public.stderr or public.stdout).strip()[:160]}\n"
            "A profile that refuses everything contains nothing, it breaks the "
            "service."
        ),
        fr=(
            f"La lecture publique de {PUBLIC} ne fonctionne plus : "
            f"{(public.stderr or public.stdout).strip()[:160]}\n"
            "Un profil qui refuse tout ne contient rien, il casse le service."
        ),
    )

    # LE MODE DU FICHIER PRIVÉ, vérifié AVANT d'éprouver le refus : sans cela, un
    # `chmod 000` obtiendrait le même refus sans qu'AppArmor y soit pour rien.
    mode = host.run("docker exec %s stat -c %%a %s", cid, PRIVE)
    assert mode.rc == 0 and mode.stdout.strip() == MODE_ATTENDU, message(
        en=(
            f"{PRIVE} is in mode {mode.stdout.strip() or '(unreadable)'} instead "
            f"of {MODE_ATTENDU}. Taking the read permission away does deny the "
            "read, without AppArmor having anything to do with it: the refusal "
            "must come from the profile."
        ),
        fr=(
            f"{PRIVE} est en mode {mode.stdout.strip() or '(illisible)'} au lieu "
            f"de {MODE_ATTENDU}. Retirer le droit de lecture refuse bien la "
            "lecture, sans qu'AppArmor y soit pour rien : le refus doit venir du "
            "profil."
        ),
    )

    prive = host.run("docker exec %s cat %s", cid, PRIVE)
    assert prive.rc != 0, message(
        en=(
            f"The private read of {PRIVE} succeeded: the profile does not refuse "
            "this path. It is attached and enforced, so the rule itself is "
            "missing or does not match."
        ),
        fr=(
            f"La lecture privée de {PRIVE} a réussi : le profil ne refuse pas ce "
            "chemin. Il est attaché et appliqué, donc c'est la règle elle-même "
            "qui manque ou qui ne correspond pas."
        ),
    )
    assert "Permission denied" in prive.stderr, message(
        en=(
            f"The private read failed, but not on a permission refusal:\n"
            f"  {prive.stderr.strip()[:200]}\n"
            "A missing file would fail the same way while proving nothing about "
            "the profile."
        ),
        fr=(
            f"La lecture privée a échoué, mais pas sur un refus de permission :\n"
            f"  {prive.stderr.strip()[:200]}\n"
            "Un fichier absent échouerait de la même façon sans rien prouver du "
            "profil."
        ),
    )
