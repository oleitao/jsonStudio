

snapcraft login                 # autentica

# on JsonStudio folder run follow comand: snapcraft --build-for=amd64
snapcraft pack --debug
snapcraft --build-for=amd64

snapcraft push jsonstudio_<version>_<arch>.snap
snapcraft status jsonstudio
# quando estiver ok:
# 1) Vê as revisões já no Store (e as arquiteturas)
snapcraft list-revisions jsonstudio

# 2) Escolhe a revisão que corresponde ao teu arm64 e liberta para edge (ou stable)
snapcraft release jsonstudio <REVISAO_ARM64> edge
# quando estiver ok:
snapcraft release jsonstudio <REVISAO_ARM64> stable

# __________________________________________________________

# 0) optional: disconnect VPN/proxy temporarily

# 1) Check multipass is healthy
multipass version
multipass find

# 2) Reset multipass if needed
multipass stop --all || true
multipass delete --all || true
multipass purge
brew services restart multipass  # if installed via Homebrew

# 3) Update multipass
brew update && brew upgrade --cask multipass

# 4) Prove images work
multipass launch 24.04 --name test-noble --cpus 2 --memory 2G --disk 64G

# 5) Build again
snapcraft
