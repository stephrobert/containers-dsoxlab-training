# Merge once, isolate by project

Three checks measure merged settings and actual HTTP identity, then replace each
environment on its own VM with fresh persistent data. The setup builds the
artifact once and transfers its unchanged archive to the second VM. Both
running image IDs must match the protected prepared image digest; the Compose
declarations must not request a deployment build. Base file hashing rejects
changes to shared configuration. Tests restore data and cleanup removes only both
lab projects and the labeled image. The image build installs busybox-extras.
