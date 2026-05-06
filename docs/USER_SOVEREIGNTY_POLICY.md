# FireDM User Sovereignty Policy

## Preamble

The user, not the developer, holds supreme authority over which features are
active in their instance of FireDM. This policy overrides all other policies,
guidelines, and architectural decisions — **except Article 8**.

---

## Article 1 — No Silent Disabling

No feature may be disabled, blocked, or gated without a corresponding
user-facing control (toggle, checkbox, dropdown, or text entry) in Settings or
the Advanced panel. Every default-off setting must have a documented path to
enable it.

## Article 2 — No Permanent Policy Override (except §8)

No policy document, security review, or release checklist may permanently
disable a user-enabling toggle, except as explicitly listed in Article 8.
Policies may recommend defaults, warn of risks, or require acknowledgment
dialogs, but the final decision belongs to the user.

## Article 3 — Persistence

All user feature choices are persisted to `setting.cfg` via `settings_keys` in
`firedm/config.py`. The application must not reset user preferences on version
upgrades. Any key added to `settings_keys` is a contract commitment; removing
it constitutes a breaking change and requires a migration entry in
`CHANGELOG-COMPILED.md`.

## Article 4 — Transparency

When a feature is blocked by default, the GUI must display:
- The exact reason for blocking (shown in Plugin Manager with red `[BLOCKED:]` label)
- A direct path to enable it (toggle location documented in the label)
- Whether the block is permanent (§8) or user-overridable

## Article 5 — No Remote Kill Switches

FireDM must not contain mechanisms for remotely disabling features. Update
checks inform users of new versions but must not deactivate existing
functionality. The `disable_update_feature` flag provides a local kill switch
for the update system itself; it is user-controlled and not remotely settable.

## Article 6 — Developer Accountability

Any pull request that introduces a feature gate must include:

1. The GUI toggle implementation in Settings or the Advanced panel
2. The config key added to `settings_keys`
3. Policy documentation update in the relevant `docs/` file
4. Test coverage for both enabled and disabled states
5. Security review annotation if the feature has risk implications

## Article 7 — Override Hierarchy

In case of conflict between policies, this User Sovereignty Policy takes
precedence over:

- Engineering-incomplete blocking (`USER_OVERRIDABLE_BLOCKED` in `policy.py`)
- Release policies (user may use pre-release features at own risk)
- Architecture decisions (user may prefer legacy code paths)
- Optional dependency policies (user may install extra packages)

This policy does **not** take precedence over Article 8.

---

## Article 8 — Permanent Carve-Out: DRM and Legal Barriers

**User sovereignty does not extend to circumventing legal protection
mechanisms.** The following features are permanently blocked regardless of any
user toggle, master gate, or future policy revision:

| Feature ID | Reason |
|------------|--------|
| `drm_decryption` | DRM bypass, protected-media circumvention, license-server access, and media-key extraction are prohibited under DMCA §1201 (USA), EU EUCD Art. 6, and equivalent statutes worldwide. No user acknowledgment can transfer this legal liability to the developer. |

These features reside in `PERMANENTLY_BLOCKED` in `firedm/plugins/policy.py`
and have no corresponding `enable_plugin_*` config key. They cannot be enabled
via the Advanced panel or any other mechanism.

**Rationale**: User sovereignty is a contract between FireDM and its users.
It does not override third-party legal obligations. Adding a "user accepts
responsibility" dialog would not insulate the project from DMCA liability;
only omitting the capability entirely does.

---

## Implementation Reference

| Concept | Location |
|---------|----------|
| Permanent blocks | `firedm/plugins/policy.py` → `PERMANENTLY_BLOCKED` |
| User-overridable blocks | `firedm/plugins/policy.py` → `USER_OVERRIDABLE_BLOCKED` |
| Advanced feature master gate | `config.advanced_features_enabled` |
| Per-plugin overrides | `config.enable_plugin_<id>` |
| GUI Advanced panel | `firedm/tkview.py` → `create_advanced_tab()` |
| Persistence contract | `firedm/config.py` → `settings_keys` |
| Test coverage | `tests/test_user_sovereignty.py` |
