# Prove persistence with new writes

The supplied image initializes only missing data. Three checks measure the
named-volume mount, force-recreation and down/up without volume removal.
Random trial writes distinguish real persistence from repeatedly copying the seed.
Tests restore the original content; cleanup deletes only this project's resources
and owner-labeled image. No host reboot is required or attested.
