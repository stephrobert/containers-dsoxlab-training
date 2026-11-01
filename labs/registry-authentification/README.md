# A private registry, not merely an encrypted registry

Setup provides fresh TLS trust and a product, but no access control or Docker
login. Credentials are generated per run and never versioned. This lab is
self-contained and does not require the previous TLS lab's state.

Three checks measure anonymous and wrong-credential rejection, retrieval with
the saved client login, and a fresh-product push/remove/pull round trip.
Each begins with the access-control requirement, so the initial score is zero.
Removing the registry-specific CA temporarily must make Docker reject TLS;
the check restores it even on failure.

The dedicated client directory avoids modifying pre-existing global Docker
credentials. Cleanup removes only named lab objects and owner-labeled images,
including build intermediates; registry data uses a host directory, not an
anonymous volume. No daemon-wide insecure exception is required.
