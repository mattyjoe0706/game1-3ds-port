# Container and CI build handoff

The engine boundary is native C + libctru/citro2d/citro3d. Unity is not an engine dependency. The bundled Unity compiler was used only to execute portable C tests via WebAssembly.

**No container/CI/native build has run in this session.** Docker/Podman and an accessible CI runner were not found. No CIA has been generated. The procedures below are prepared for a host with the required access; they do not override this session's permissions.

## Official container

The [official devkitPro Dockerfile](https://github.com/devkitPro/docker/blob/master/devkitarm/Dockerfile) installs `3ds-dev` and 3DS port libraries. The base image includes Python, Make, and host build tools. Default image: `devkitpro/devkitarm:20260610`, a published dated tag. Tags can move: the local wrapper resolves an installed image to its immutable image ID, builds using that ID, and records the ID and repository digests. It does not claim a preverified image digest.

On a host with Docker, from the extracted source project:

```text
python tools/build_container.py --pull --output build-first
```

This pulls the official image, checks the Docker daemon, and builds ELF/3DSX. The compiler step runs without network access, with source mounted read-only and a separate writable output directory. No host package installer or privileged container is used. Docker still needs a running engine and permission to use it; a pull cannot work without those prerequisites.

For CIA, provide a **Linux makerom executable matching the container architecture**:

```text
python tools/build_container.py --pull --output build-cia-first --makerom PATH_TO_LINUX_MAKEROM
```

Makerom is not assumed to be bundled with devkitPro. Windows `.exe` files cannot run in this Linux container. The alternative CI workflow builds the official makerom source itself. The host executable must have its executable permission set before mounting it. Each attempt needs an empty output directory so stale binaries cannot be mistaken for a successful build.

`--print-command` displays the exact argument list without running Docker. Network restrictions or missing tools cause a failure, not a fallback to another host.

## GitHub Actions

Use the separately generated **source-only build ZIP** as the root of an existing repository. It includes `.github/workflows/native-build.yml`, but no WBFS, extracted archives, SD data, or converted course data. A `.gitignore` also excludes those assets. No repository was created or uploaded during this work.

The **Native 3DS inspector build** workflow runs on a push to `main`, or manually through Actions. It:

1. Uses the dated official devkitPro container on an Ubuntu runner.
2. Checks out the official `makerom-v0.19.0` release and builds its included dependencies, then makerom. Records its resolved commit and the installed package versions.
3. Runs source-only Python and host C checks. The local game-data test is explicitly skipped when its fixture is absent.
4. Builds ELF/3DSX/CIA using the project's native script and returns binaries, hashes, source hashes, package/compiler provenance, and logs. No deployment, publication, or device installation is performed.

Download the `nsmbw-inspector-unvalidated` artifact after the run. If the job failed, it may contain only logs or partial outputs. Check `build-report.json`: only `built_unvalidated` means the tool commands all succeeded. That status does not establish CIA launch, native rendering correctness, gameplay, or performance. Share the artifact/logs back with this task for integration and fixes.

The workflow must be committed to a repository with Actions enabled before it can run. This workspace has no accessible repository/runner selected yet. An available repository URL or build-host connection is required for me to dispatch and inspect an actual build.

## Offline package alternative

An already prepared, complete devkitPro prefix can be used directly with `tools/build_native.py --devkitpro PATH --output NEW_DIRECTORY --cia --makerom PATH`. This supports a user-writable prefix and needs no install during the build.

Manually unpacking packages must preserve the full dependency tree, correct host binaries, library/tool versions, and executable links. `3ds-dev` is a package group, not a single self-contained compiler archive. A Linux toolchain will not run directly on this Windows host. Individual downloaded packages have not been supplied, and this session has not downloaded or unpacked an offline toolchain. The official container is the preferred path once a usable host is available.

## Emulator and hardware gates

After successful compilation, test startup, both area loads, missing/corrupt data handling, pause, area changes, scrolling, and exit in a compatible emulator configured as a New 3DS. Keep emulator results labeled separately. No emulator test has run here, and no frame-rate or memory numbers are available.

On the actual New 3DS XL, verify CIA installation, descriptor behavior, rendering and capture output. The current program is a **placement viewer**; its telemetry establishes only viewer/loader feasibility. Reconstructed collision, stage, actor, graphics and audio systems plus a complete faithful playthrough are still required before assessing the game's 240p/60 fps target.
