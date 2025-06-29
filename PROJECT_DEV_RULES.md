# KIVY\_UI — Project Development Rules

> **Audience:** LLM agents (and humans) who contribute code or configuration to this repo.
>
> **Purpose:** guarantee that Linux **and** Android builds stay green, reproducible, and easy to iterate on.

---

## 1 · Repository Anatomy

| Path                        | What belongs here                                                                                 | Never put here                             |
| --------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `chat_ui/`                  | Kivy widgets, screens, networking, pure‑Python logic.<br>*Must run unmodified on every platform.* | OS checks, JNI, desktop libraries          |
| `platform_utils/android.py` | Helpers that call Android‑only APIs via PyJNIus.                                                  | Any imports used on desktop (e.g. `plyer`) |
| `platform_utils/desktop.py` | Helpers that call Linux‑only APIs (`plyer`, `dbus`, etc.).                                        | PyJNIus or Android permissions             |
| `main.py`                   | App entry‑point, platform‑agnostic.                                                               | Direct JNI / desktop calls                 |
| `pyproject.toml`            | **Single source of truth** for dependencies.                                                      | Platform logic, secrets                    |
| `buildozer.spec`            | Android build recipe (auto‑generated, keep in Git).                                               | Desktop packaging                          |
| `KivyChatUI.spec`           | PyInstaller recipe for Linux.                                                                     | Android packaging                          |
| `.github/workflows/`        | CI robots: `android-build.yml`, `linux-build.yml`.                                                | Business logic                             |
| `tests/`                    | Fast smoke tests; **must pass** on both CI jobs.                                                  | Long‑running or UI tests                   |

---

## 2 · Branch & Merge Policy

| Branch    | Purpose                                        | Merge Gate                                     |
| --------- | ---------------------------------------------- | ---------------------------------------------- |
| `main`    | Source‑of‑truth for desktop‑first development. | **linux-build** workflow green + tests green   |
| `android` | Mirrors `main` plus Android tweaks.            | **android-build** workflow green + tests green |

* **Rule:** Never commit directly to protected branches. Open a PR; CI must pass on *all* matrix jobs.
* **Fast‑forward:** Sync `android` with `main` at least once per week (agent task `sync‑android`).

---

## 3 · Dependency Governance

```toml
[project.optional-dependencies]
android = ["pyjnius", "android_permissions"]
desktop = ["plyer", "dbus-python"]
dev     = ["black", "pytest", "buildozer"]
```

* **Rule:** Every new requirement **must** land in `pyproject.toml`; choose the right extra.
* **Agents**: run `uv sync --extra dev --extra desktop` before tests.

---

## 4 · Adding Platform‑Specific Code

1. Write identical *function signature* in both `platform_utils/android.py` and `platform_utils/desktop.py`.
2. Implement real logic in the relevant file; stub (`pass` or log) in the other.
3. Add/extend a smoke test in `tests/` that calls the new helper.
4. Commit both files + test in a single PR.

**Never** import `pyjnius` or `plyer` outside `platform_utils/`.

---

## 5 · Local Dev Commands

| Task                         | Command                                                          |
| ---------------------------- | ---------------------------------------------------------------- |
| Format + test (desktop)      | `uv run black . && uv run pytest -q`                             |
| Run app (desktop)            | `uv run python main.py`                                          |
| Android build + deploy (USB) | `buildozer -v android debug deploy run logcat`                   |
| Clean Buildozer cache        | `buildozer android clean`                                        |
| Refresh CI builds            | `git push` (desktop) or `git push --set-upstream origin android` |

---

## 6 · CI Expectations

* **linux-build.yml**: installs `.[desktop]`, runs pytest, bundles with PyInstaller, uploads artefact.
* **android-build.yml**: dockerised Buildozer, installs `.[android]`, runs pytest, assembles debug APK.
* **Fail‑fast:** Agent must halt if either job fails; push a fix before continuing.

---

## 7 · Commit & PR Conventions

* Conventional commit titles (`feat:`, `fix:`, `chore:` …).
* One logical change per PR (small is beautiful).
* PR description must list:

  * **What changed**
  * **Why** (link task‑id if any)
  * **How to test** (commands)

---

## 8 · Release Procedure

1. Ensure both branches green.
2. `git tag -a vX.Y.Z -m "brief notes"; git push --tags`.
3. CI attaches Linux binary + APK to tag.
4. Draft GitHub Release notes (agent may auto‑generate from commits).

---

## 9 · Agent‑Specific Rules

| ID  | Rule                                                                      |
| --- | ------------------------------------------------------------------------- |
| A‑1 | **Fail‑fast & rollback** on any test failure.                             |
| A‑2 | Use `Path` API; avoid hard‑coded absolute paths.                          |
| A‑3 | Save artefacts (test logs, screenshots) to `artefacts/` for human review. |
| A‑4 | Ask for clarification if requirement is ambiguous.                        |
| A‑5 | Keep build cache (`~/.buildozer`) intact between tasks for speed.         |

---

## 10 · Troubleshooting Quick Hits

| Symptom                            | Likely cause                          | Fix                                                                |
| ---------------------------------- | ------------------------------------- | ------------------------------------------------------------------ |
| `adb devices` shows *unauthorized* | Phone didn’t accept RSA key           | Replug phone, accept prompt, `adb kill-server && adb start-server` |
| App crashes on launch              | Missing permission or wrong JNI class | Check logcat, update `android.permissions` or class path           |
| CI fails only on Android           | New import uses desktop‑only lib      | Move code into `platform_utils/desktop.py`                         |
| Very slow Buildozer build          | Cache wiped                           | Verify `~/.buildozer`, avoid `clean` unless necessary              |

---

> **Remember:** The engine (`chat_ui/`) never changes for the road—it’s the plug adaptor (`platform_utils/`) that swaps when you cross borders.
