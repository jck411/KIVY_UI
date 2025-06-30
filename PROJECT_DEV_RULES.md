**KIVY\_UI — Project Development Rules**

> **Audience:** LLM agents (and humans) who contribute code or configuration to this repo.
> **Purpose:** Guarantee that Linux **and** Android builds stay green, reproducible, and easy to iterate on.

---

### 1 · Repository Anatomy

The repository is organized into the following key paths:

* **chat\_ui/**

  * **What belongs here:** Kivy widgets, screens, networking, and pure-Python logic.
  * **Constraint:** Must run unmodified on every platform.
  * **What *never* to put here:** OS checks, JNI calls, or desktop-specific libraries.

* **platform\_utils/android.py**

  * **What belongs here:** Helpers that call Android-only APIs via PyJNIus.
  * **What *never* to put here:** Any imports used on desktop (e.g., `plyer`).

* **platform\_utils/desktop.py**

  * **What belongs here:** Helpers that call Linux-only APIs (`plyer`, `dbus`, etc.).
  * **What *never* to put here:** PyJNIus or Android permissions.

* **main.py**

  * **What belongs here:** App entry-point; platform-agnostic code.
  * **What *never* to put here:** Direct JNI calls or desktop-specific logic.

* **pyproject.toml**

  * **What belongs here:** **Single source of truth** for dependencies.
  * **What *never* to put here:** Platform logic or secrets.

* **buildozer.spec**

  * **What belongs here:** Android build recipe (auto-generated; keep in Git).
  * **What *never* to put here:** Desktop packaging.

* **KivyChatUI.spec**

  * **What belongs here:** PyInstaller recipe for Linux.
  * **What *never* to put here:** Android packaging.

* **.github/workflows/**

  * **What belongs here:** CI robots (`android-build.yml`, `linux-build.yml`).
  * **What *never* to put here:** Business logic.

* **tests/**

  * **What belongs here:** Fast smoke tests that **must pass** on both CI jobs.
  * **What *never* to put here:** Long-running or UI tests.

---

### 2 · Branch & Merge Policy

* **`main` branch**

  * **Purpose:** Source-of-truth for desktop-first development.
  * **Merge Gate:** The **linux-build** workflow and tests must be green.

* **`android` branch**

  * **Purpose:** Mirrors `main` plus Android-specific tweaks.
  * **Merge Gate:** The **android-build** workflow and tests must be green.

**Additional Rules:**

* Never commit directly to protected branches. Open a PR and ensure CI passes all matrix jobs.
* Fast-forward sync: merge updates from `main` into `android` at least once per week (agent task `sync-android`).

---

### 3 · Dependency Governance

Dependencies are managed in `pyproject.toml` as follows:

```toml
[project]
dependencies = [
    # Core dependencies only - no dev or platform-specific packages
    "kivy==2.3.1",
    "websockets==13.1",
]

[project.optional-dependencies]
android = ["pyjnius", "android_permissions"]  # Android-specific packages
desktop = ["plyer", "dbus-python"]           # Desktop-specific packages
dev = [
    "black",
    "pytest",
    "buildozer[dev]",                        # Required for Android builds
    "cython",                                # Required by buildozer
]
```

**Critical Rules:**

* Every requirement **must** be added to `pyproject.toml` under the appropriate section:
  * Core dependencies → `[project.dependencies]`
  * Platform-specific → `[project.optional-dependencies.android/desktop]`
  * Development tools → `[project.optional-dependencies.dev]`

* **Never** put development tools (buildozer, pytest, etc.) in `[project.dependencies]`
* **Always** include version constraints for reproducible builds
* **Avoid** duplicate dependency sections (e.g., don't use both `[tool.uv.dev-dependencies]` and `[project.optional-dependencies.dev]`)

**Agent Workflow:**

Before any development work:
```bash
# For desktop development
uv sync --extra dev --extra desktop

# For Android development
uv sync --extra dev --extra android
```

**Buildozer Setup:**
* Buildozer **must** be installed via the dev extras: `uv sync --extra dev`
* Never install buildozer globally or via pip/poetry/conda
* Always include both buildozer and cython in dev dependencies
* If buildozer is not found after sync, check PATH includes `~/.local/bin`

---

### 4 · Adding Platform-Specific Code

1. **Signature parity:** Write an identical function signature in both `platform_utils/android.py` and `platform_utils/desktop.py`.
2. **Implementation:** In the relevant file implement the real logic; in the other file provide a stub (`pass` or a log statement).
3. **Smoke Test:** Add or extend a smoke test under `tests/` that calls the new helper.
4. **Single PR:** Commit changes to both files and the new test in one pull request.

> **Never** import `pyjnius` or `plyer` outside of their respective `platform_utils/` modules.

---

### 5 · Local Dev Commands

Use the following commands during local development:

* **Format and test (desktop):**

  ```
  uv run black . && uv run pytest -q
  ```

* **Run app (desktop):**

  ```
  uv run python main.py
  ```

* **Android build + deploy (USB):**

  ```
  buildozer -v android debug deploy run logcat
  ```

* **Clean Buildozer cache:**

  ```
  buildozer android clean
  ```

* **Refresh CI builds:**

  * For desktop: `git push`
  * For android: `git push --set-upstream origin android`

---

### 6 · CI Expectations

* **linux-build.yml:**

  * Installs the `.[desktop]` extras.
  * Runs `pytest`.
  * Bundles the app with PyInstaller.
  * Uploads the artifact.

* **android-build.yml:**

  * Uses Dockerized Buildozer.
  * Installs the `.[android]` extras.
  * Runs `pytest`.
  * Assembles a debug APK.

* **Fail-fast:** If either job fails, the agent must halt and push a fix before proceeding.

---

### 7 · Commit & PR Conventions

* **Commit titles:** Use conventional prefixes (`feat:`, `fix:`, `chore:`, etc.).
* **Scope:** One logical change per PR—keep them small.
* **PR description** must include:

  * **What changed**
  * **Why:** (link task-ID if applicable)
  * **How to test:** list the commands to verify the change

---

### 8 · Release Procedure

1. Verify that both `main` and `android` branches are green.
2. Create an annotated tag and push it:

   ```
   git tag -a vX.Y.Z -m "brief notes"
   git push --tags
   ```
3. CI will attach both the Linux binary and the APK to the tag.
4. Draft GitHub Release notes (an agent may auto-generate these from commit history).

---

### 9 · Agent-Specific Rules

* **A-1:** Fail-fast & rollback on any test failure.
* **A-2:** Use the `Path` API; avoid hard-coded absolute paths.
* **A-3:** Save artifacts (test logs, screenshots) to `artefacts/` for human review.
* **A-4:** Ask for clarification if a requirement is ambiguous.
* **A-5:** Keep the build cache (`~/.buildozer`) intact between tasks for speed.

---

### 10 · Troubleshooting Quick Hits

* **`adb devices` shows *unauthorized*:**

  * **Likely cause:** Phone didn't accept the RSA key.
  * **Fix:** Replug the phone, accept the prompt, then run:

    ```
    adb kill-server && adb start-server
    ```

* **App crashes on launch:**

  * **Likely cause:** Missing permission or wrong JNI class.
  * **Fix:** Check `logcat`, update `android.permissions` or correct the class path.

* **CI fails only on Android:**

  * **Likely cause:** A new import uses a desktop-only library.
  * **Fix:** Move that code into `platform_utils/desktop.py`.

* **Very slow Buildozer build:**

  * **Likely cause:** Cache was wiped.
  * **Fix:** Verify `~/.buildozer` exists and avoid `clean` unless necessary.

---

> **Remember:** The core engine (`chat_ui/`) never changes for the road—it's the plug adaptor (`platform_utils/`) that swaps when you cross borders.
