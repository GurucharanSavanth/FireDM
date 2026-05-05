# Documentation Index

## Agent Instruction Files
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| `AGENTS.md` | Primary Codex/general-agent rules | agent-facing | recreated and hardened as primary authority |
| `AGENT.md` | Companion for tools or humans that look for singular filename | agent-facing | converted to companion to reduce authority drift |
| `CLAUDE.md` | Claude Code rules and reviewer limits | agent-facing | created |
| `.claude/agents/architecture-reviewer.md` | Read-only Claude architecture reviewer | Claude subagent | created from locally verified `.claude/agents/` convention |
| `.claude/agents/security-reviewer.md` | Read-only Claude security reviewer | Claude subagent | created from locally verified `.claude/agents/` convention |
| `.claude/agents/documentation-reviewer.md` | Read-only Claude documentation reviewer | Claude subagent | created from locally verified `.claude/agents/` convention |
| `.claude/agents/validation-reviewer.md` | Read-only Claude validation reviewer | Claude subagent | created from locally verified `.claude/agents/` convention |
| `docs/agent/PROJECT_MEMORY.md` | Persistent repo-local memory | agent-facing | created |
| `docs/agent/ARCHITECTURE_MAP.md` | Evidence-labeled architecture map | architecture | created |
| `docs/agent/SESSION_HANDOFF.md` | Continuation state and locks | agent-facing | created |
| `docs/agent/MULTI_AGENT_PROTOCOL.md` | Bounded multi-agent workflow | agent-facing | created |
| `docs/agent/VALIDATION_MATRIX.md` | Validation command map | validation | created |
| `docs/agent/SECURITY_BOUNDARIES.md` | Permanent safety rules | security | created |
| `docs/agent/REFACTOR_ROADMAP.md` | Staged modernization plan | architecture/refactor | created |
| `docs/agent/DOCUMENTATION_INDEX.md` | Markdown ownership map | documentation | created |

## Human-Facing Docs
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| `README.md` | Main human project overview, setup, testing, packaging | human-facing | preserved unchanged |
| `contributors.md` | Contributor credits | human-facing | preserved unchanged |
| `todo.md` | Short legacy task list | human-facing | preserved unchanged |
| `bootstrap/windows-dev-setup.md` | Windows setup guide | setup | preserved unchanged |
| `BASELINE_AUDIT.md` | Baseline audit summary | audit | preserved unchanged |
| `docs/user_guide.md` | End-user feature guide | human-facing | preserved unchanged |
| `docs/user/USER_GUIDE.md` | Modernization user guide | human-facing | created |
| `docs/user/ENGINE_SELECTION.md` | Engine-selection user guide | human-facing | created |
| `docs/user/BUILT_IN_HELP.md` | Built-in help plan | human-facing | created |
| `docs/user/TROUBLESHOOTING.md` | Troubleshooting plan | human-facing | created |
| `docs/developer_guide.md` | Developer guidance | human-facing | preserved unchanged |
| `docs/frontend/GUI_MIGRATION_PLAN.md` | Staged FireDM GUI modernization plan for the active Tk path | frontend/architecture | changed |
| `docs/frontend/UI_PARITY_MATRIX.md` | Existing UI feature parity tracker | frontend/validation | created |
| `docs/developer/CONTRIBUTING_MODERNIZATION.md` | Modernization contribution rules | developer | created |
| `docs/developer/BUILD_SCRIPT_UPDATE_POLICY.md` | Canonical build-script impact policy for future patches | developer/release | created |
| `docs/developer/DEPENDENCY_MODERNIZATION_PLAN.md` | Dependency family inventory and upgrade policy | developer/dependency | created |
| `docs/developer/IMPLEMENTATION_LAYERS.md` | One-paragraph-per-layer developer view of the 19-layer modernization program | developer | created |
| `docs/developer/TESTING_STRATEGY.md` | Modernization testing strategy | developer/validation | created |
| `docs/developer/VALIDATION_PIPELINE.md` | Per-layer validation gates and planned validation extensions | developer/validation | created |
| `docs/known-issues.md` | Known issues and deferred work | human-facing | preserved unchanged |
| `docs/windows-bootstrap.md` | Windows bootstrap guide | setup | preserved unchanged |
| `docs/windows-bootstrap-log.md` | Windows bootstrap log | setup evidence | preserved unchanged |
| `docs/windows-build.md` | Windows build and packaging guide | release/setup | updated for canonical root `windows-build.ps1` |

## Architecture Docs
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| `docs/architecture.md` | Short architecture overview | architecture | preserved, summarized into `ARCHITECTURE_MAP.md` |
| `docs/architecture/MODERN_ARCHITECTURE.md` | Modernization target architecture | architecture | created |
| `docs/architecture/MODERNIZATION_MASTER_PLAN.md` | Authoritative status table + dependency graph for the 19-layer modernization program | architecture | created |
| `docs/architecture/ENGINE_PLUGIN_SYSTEM.md` | Engine abstraction and adapter plan | architecture | created |
| `docs/architecture/UPDATE_SYSTEM.md` | In-app updater architecture | architecture | created as design-only plan |
| `docs/architecture/UI_UX_PLAN.md` | Incremental UI modernization plan | architecture/UI | created as design-only plan |
| `docs/architecture/TOOLCHAIN_DECISIONS.md` | Official-doc-backed toolchain decisions | architecture/release | created |
| `docs/video-pipeline-architecture.md` | Video pipeline map | architecture | preserved, summarized into `ARCHITECTURE_MAP.md` |
| `docs/legacy-refactor-plan.md` | Refactor boundaries for large modules | architecture/refactor | preserved, summarized into `REFACTOR_ROADMAP.md` |
| `docs/extractor-migration-policy.md` | Extractor dependency policy | architecture/dependency | preserved unchanged |
| `docs/dependency-strategy.md` | Dependency strategy | dependency | preserved unchanged |
| `docs/dependency-modernization-review.md` | Dependency review notes | dependency | preserved unchanged |
| `docs/dependency-migration-notes.md` | Migration notes | dependency | preserved unchanged |
| `docs/packaging-modernization.md` | Packaging modernization notes | release/architecture | preserved unchanged |
| `docs/pyproject-migration-notes.md` | Pyproject migration notes | packaging | preserved unchanged |
| `docs/p0-youtube-bug-baseline.md` | YouTube bug baseline | diagnostics | preserved unchanged |
| `docs/p0-youtube-bug-fix.md` | YouTube bug fix notes | diagnostics | preserved unchanged |
| `docs/packaged-video-validation.md` | Packaged video validation | validation | preserved unchanged |
| `docs/regression-strategy.md` | Regression strategy | validation | preserved unchanged |
| `docs/runtime-diagnostics.md` | Runtime diagnostics guide | diagnostics | preserved, summarized into validation/security docs |
| `docs/tooling-policy.md` | Tooling policy | validation/tooling | preserved, summarized into `VALIDATION_MATRIX.md` |
| `docs/testing.md` | Test commands and policy | validation | preserved, summarized into `VALIDATION_MATRIX.md` |

## Validation Docs
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| `artifacts/build_release_update/00_discovery.md` | Prior release discovery | artifact | preserved unchanged |
| `artifacts/build_release_update/01_build_id_design.md` | Build ID design | artifact | preserved unchanged |
| `artifacts/build_release_update/02_scripts_changed.md` | Release script change list | artifact | preserved unchanged |
| `artifacts/build_release_update/03_github_release_dry_run.md` | Release dry-run record | artifact | preserved unchanged |
| `artifacts/build_release_update/04_workflow_review.md` | Workflow review | artifact | preserved unchanged |
| `artifacts/build_release_update/05_validation_log.md` | Validation log | artifact | preserved unchanged |
| `artifacts/build_release_update/06_reviewer_packet.md` | Reviewer packet | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/00_discovery.md` | Dependency discovery | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/01_dependency_inventory.md` | Dependency inventory | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/02_deprecation_and_docs_review.md` | Deprecation/docs review | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/03_import_warning_sweep.md` | Import warning sweep | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/04_dependency_declaration_cleanup.md` | Declaration cleanup | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/05_scripts_folder_review.md` | Scripts folder review | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/06_portable_package_completeness.md` | Portable completeness | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/07_ffmpeg_policy.md` | FFmpeg policy | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/08_github_actions_review.md` | Actions review | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/09_validation_log.md` | Validation log | artifact | preserved unchanged |
| `artifacts/dependency_maintenance/10_reviewer_packet.md` | Reviewer packet | artifact | preserved unchanged |
| `artifacts/final_wrapup/00_discovery.md` | Final wrap-up discovery | artifact | preserved unchanged |
| `artifacts/final_wrapup/01_dirty_tree_classification.md` | Dirty-tree classification | artifact | preserved unchanged |
| `artifacts/final_wrapup/02_gitattributes_review.md` | Attributes review | artifact | preserved unchanged |
| `artifacts/final_wrapup/03_gitignore_review.md` | Ignore rules review | artifact | preserved unchanged |
| `artifacts/final_wrapup/04_actions_review.md` | Actions review | artifact | preserved unchanged |
| `artifacts/final_wrapup/05_release_scripts_review.md` | Release scripts review | artifact | preserved unchanged |
| `artifacts/final_wrapup/06_tests_review.md` | Tests review | artifact | preserved unchanged |
| `artifacts/final_wrapup/07_docs_review.md` | Docs review | artifact | preserved unchanged |
| `artifacts/final_wrapup/08_artifacts_policy.md` | Artifacts policy | artifact | preserved unchanged |
| `artifacts/final_wrapup/09_validation_log.md` | Validation log | artifact | preserved unchanged |
| `artifacts/final_wrapup/10_push_preparation.md` | Push prep notes | artifact | preserved unchanged |
| `artifacts/unified_version_build/00_discovery.md` | Version-build discovery | artifact | preserved unchanged |
| `artifacts/unified_version_build/01_version_source_audit.md` | Version source audit | artifact | preserved unchanged |

## Security Docs
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| `artifacts/security/attack_surface_map.md` | Security attack-surface map | artifact/security | preserved unchanged |
| `artifacts/security/audit_2026-04-26.md` | Security audit record | artifact/security | preserved unchanged |
| `artifacts/security/candidate_ledger.md` | Candidate security ledger | artifact/security | preserved unchanged |
| `artifacts/security/command_log.md` | Security audit command log | artifact/security | preserved unchanged |
| `artifacts/security/verified_audit_report.md` | Verified security report | artifact/security | preserved unchanged |
| `artifacts/windows_installer/09_security_review.md` | Installer security review | artifact/security | preserved unchanged |
| `artifacts/windows_installer_phase2/02_path_uninstall_safety_review.md` | Path/uninstall safety review | artifact/security | preserved unchanged |
| `docs/release/CODE_SIGNING.md` | Signing status/policy | release/security | preserved unchanged |
| `docs/release/FFMPEG_BUNDLING.md` | FFmpeg bundling boundary | release/security | preserved unchanged |
| `docs/release/THIRD_PARTY_BUNDLED_COMPONENTS.md` | Bundled component status | release/security | preserved unchanged |
| `docs/security/SECURITY_MODEL.md` | Modernized security model | security | created |
| `docs/security/UPDATER_THREAT_MODEL.md` | Updater threat model | security | created |

## Release Docs
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| `docs/release/BUILD_ID_POLICY.md` | Unified build-code policy | release | preserved unchanged |
| `docs/release/BUILD_SYSTEM.md` | Build orchestrator design and backend matrix | release | created |
| `docs/release/CHANGELOG_COMPILATION.md` | Canonical release changelog compilation rules | release | created |
| `docs/release/COMPILER_PIPELINE_PLAN.md` | PyInstaller/Nuitka staged compiler pipeline plan | release/build | created |
| `docs/release/COMPATIBILITY_MATRIX.md` | OS/runtime compatibility matrix | release | created |
| `docs/release/DEPENDENCY_POLICY.md` | Release dependency policy | release | preserved unchanged |
| `docs/release/RELEASE_ARTIFACT_LAYOUT.md` | Root `release` artifact contract | release | created |
| `docs/release/RUNTIME_VERSION_STRATEGY.md` | Python runtime lane strategy | release/runtime | created |
| `docs/release/GITHUB_RELEASES.md` | Release publishing workflow | release | preserved unchanged |
| `docs/release/LINUX_BUILD.md` | Linux build lane | release | preserved unchanged |
| `docs/release/LINUX_PORTABLE.md` | Linux portable archive | release | preserved unchanged |
| `docs/release/RELEASE_CHECKLIST.md` | Release checklist | release | preserved unchanged |
| `docs/release/WINDOWS_INSTALLER.md` | Windows installer lane | release | preserved unchanged |
| `docs/release/WINDOWS_LEGACY_SUPPORT.md` | Legacy Windows support | release | preserved unchanged |
| `docs/release/WINDOWS_MANUAL_QA.md` | Windows manual QA | release | preserved unchanged |
| `docs/release/WINDOWS_PORTABLE.md` | Windows portable package | release | preserved unchanged |
| `docs/release/SELF_UPDATER.md` | Self-updater release design | release/security | created |
| `artifacts/windows_installer/00_repo_packaging_discovery.md` | Packaging discovery | artifact/release | preserved unchanged |
| `artifacts/windows_installer/01_packaging_tool_decision.md` | Packaging tool decision | artifact/release | preserved unchanged |
| `artifacts/windows_installer/02_architecture_matrix.md` | Installer architecture matrix | artifact/release | preserved unchanged |
| `artifacts/windows_installer/03_runtime_bundle_layout.md` | Runtime bundle layout | artifact/release | preserved unchanged |
| `artifacts/windows_installer/04_environment_variable_policy.md` | Environment variable policy | artifact/release | preserved unchanged |
| `artifacts/windows_installer/05_installer_feature_matrix.md` | Installer feature matrix | artifact/release | preserved unchanged |
| `artifacts/windows_installer/06_upgrade_repair_uninstall_design.md` | Upgrade/repair/uninstall design | artifact/release | preserved unchanged |
| `artifacts/windows_installer/07_shortcut_design.md` | Shortcut design | artifact/release | preserved unchanged |
| `artifacts/windows_installer/08_update_strategy.md` | Update strategy | artifact/release | preserved unchanged |
| `artifacts/windows_installer/10_license_inventory.md` | License inventory | artifact/release | preserved unchanged |
| `artifacts/windows_installer/11_legacy_windows_feasibility.md` | Legacy Windows feasibility | artifact/release | preserved unchanged |
| `artifacts/windows_installer/12_performance_budget.md` | Performance budget | artifact/release | preserved unchanged |
| `artifacts/windows_installer/13_validation_plan.md` | Validation plan | artifact/release | preserved unchanged |
| `artifacts/windows_installer/14_validation_log.md` | Validation log | artifact/release | preserved unchanged |
| `artifacts/windows_installer/15_release_handover.md` | Release handover | artifact/release | preserved unchanged |
| `artifacts/windows_installer/16_review_packet.md` | Review packet | artifact/release | preserved unchanged |
| `artifacts/windows_installer/17_ffmpeg_bundling_decision.md` | FFmpeg bundling decision | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/00_previous_claims_verification.md` | Prior claims check | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/01_installer_bootstrap_review.md` | Installer bootstrap review | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/03_version_upgrade_repair_review.md` | Upgrade/repair review | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/04_gui_smoke_validation.md` | GUI smoke validation | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/05_upgrade_downgrade_fixture_results.md` | Upgrade/downgrade fixtures | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/06_ffmpeg_bundling_decision.md` | FFmpeg bundling decision | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/07_architecture_lane_status.md` | Architecture lane status | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/08_universal_bootstrapper_status.md` | Universal bootstrapper status | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/09_signing_status.md` | Signing status | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/10_github_actions_status.md` | Actions status | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/11_validation_log.md` | Validation log | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/12_release_readiness.md` | Release readiness | artifact/release | preserved unchanged |
| `artifacts/windows_installer_phase2/13_reviewer_packet.md` | Reviewer packet | artifact/release | preserved unchanged |

## Additional Artifact Docs
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| `artifacts/baseline/environment_summary.md` | Baseline environment summary | artifact | preserved unchanged |
| `artifacts/dependencies/official_docs_reviewed.md` | Dependency docs review notes | artifact/dependency | preserved unchanged |
| `artifacts/dependencies/replacement_matrix.md` | Dependency replacement matrix | artifact/dependency | preserved unchanged |
| `artifacts/diagnostics/controller_boundary_refactor_map.md` | Controller boundary map | artifact/diagnostics | preserved unchanged |
| `artifacts/diagnostics/failure_surface_report.md` | Failure surface report | artifact/diagnostics | preserved unchanged |
| `artifacts/diagnostics/observability_matrix.md` | Observability matrix | artifact/diagnostics | preserved unchanged |
| `artifacts/extractor/deprecated_api_inventory.md` | Deprecated extractor API inventory | artifact/extractor | preserved unchanged |
| `artifacts/extractor/extractor_dependency_audit.md` | Extractor dependency audit | artifact/extractor | preserved unchanged |
| `artifacts/extractor/extractor_inventory.md` | Extractor inventory | artifact/extractor | preserved unchanged |
| `artifacts/ffmpeg/merge_command_audit.md` | FFmpeg merge command audit | artifact/ffmpeg | preserved unchanged |
| `artifacts/final/commit_phase_summary.md` | Final phase summary | artifact | preserved unchanged |
| `artifacts/final/hand_over_checklist.md` | Handoff checklist | artifact | preserved unchanged |
| `artifacts/final/remaining_risks.md` | Remaining risk record | artifact | preserved unchanged |
| `artifacts/final/root_cause_analysis.md` | Root-cause analysis | artifact | preserved unchanged |
| `artifacts/final/technical_decisions.md` | Technical decisions | artifact | preserved unchanged |
| `artifacts/final/validation_summary.md` | Validation summary | artifact | preserved unchanged |
| `artifacts/full_codebase_repair/00_baseline.md` | Full-codebase repair baseline | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/01_architecture_map.md` | Full-codebase architecture map | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/02_issue_inventory.md` | Issue inventory | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/03_baseline_validation.md` | Baseline validation | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/04_class_inheritance_review.md` | Class inheritance review | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/05_warning_audit.md` | Warning audit | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/06_patch_plan.md` | Patch plan | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/07_changes_made.md` | Changes made | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/08_tests_added_or_updated.md` | Test change record | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/09_validation_log.md` | Validation log | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/10_security_review.md` | Security review | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/11_platform_review.md` | Platform review | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/12_packaging_review.md` | Packaging review | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/13_handover.md` | Handover notes | artifact/repair | preserved unchanged |
| `artifacts/full_codebase_repair/14_review_packet.md` | Review packet | artifact/repair | preserved unchanged |
| `artifacts/packaging/packaging_decision_record.md` | Packaging decision record | artifact/packaging | preserved unchanged |
| `artifacts/regression/test_matrix.md` | Regression test matrix | artifact/validation | preserved unchanged |
| `dist/FireDM_release_notes_20260428_V2.md` | Generated release notes | generated release artifact | preserved unchanged |
| `dist/release-body.md` | Generated release body | generated release artifact | preserved unchanged |
| `release/FireDM-2022.2.5-windows-x64/release-body.md` | Historical release body | generated release artifact | preserved unchanged |

## Deprecated/Replaced Docs
| Path | Purpose | Classification | Decision |
| --- | --- | --- | --- |
| previous tracked `AGENTS.md` | Former concise repo guidelines | agent-facing | replaced by primary `AGENTS.md` plus companion `AGENT.md`; unique facts preserved |
| legacy AppImage/exe notes in docs and scripts | Historical packaging reference | release | preserved; not current preferred release path |

## Update Rules
- Add every new Markdown file to this index in the right section.
- Mark whether the file is human-facing, agent-facing, architecture, validation, security, release, artifact, setup, or audit.
- Do not remove a Markdown file from this index before preserving its useful content elsewhere.
- Keep agent-facing docs free of network project authority language and unresolved placeholder markers.
- Keep `AGENTS.md` as primary authority; `AGENT.md` remains companion unless a future local tool check proves a different load order.
