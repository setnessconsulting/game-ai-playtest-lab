# CI and pull-request verification

Repository: `setnessconsulting/game-ai-playtest-lab`
Risk tier: `LOW` in the live `project-jenkins-config` policy.
Routine PR workflow: `.github/workflows/ci.yml` (GitHub Actions, same-repository PRs only)
Jenkins catalog profile: `game-ai-playtest-lab-python312` (qualification does not establish a merge gate)
Owner-controlled Actions fallback: `.github/workflows/jenkins-fallback.yml` (manual `workflow_dispatch`, owner-controlled, exact-SHA)
Fork PR support: `not qualified`
Deployment boundary: verification does not deploy; release and deployment remain outside CI.

- Before authoring or reviewing a pull request, refresh the current PR head SHA, live check statuses and sources, and branch-protection requirements. State which checks are required by live GitHub protection.
- LOW-risk repositories use GitHub Actions for routine pull request verification. The `ci.yml` workflow skips build and test work for documentation-only changes and rejects fork pull requests before checkout.
- The Jenkins profile records qualification evidence but does not make Jenkins a merge gate. If live GitHub protection requires `jenkins-pr-gate`, require a completed success on the exact current PR head from App ID `5043075`; otherwise treat Jenkins as supplemental.
- `.github/workflows/jenkins-fallback.yml` remains an owner-controlled manual exact-SHA fallback. Do not dispatch Jenkins for routine PR verification.
- Never run a pull-request-supplied Jenkinsfile. Never expose the GitHub App private key, Checks-write credential, production secret, controller data, Docker socket, or persistent agent state to repository code.
- Fork verification stays disabled until the per-run untrusted sandbox is qualified. A maintainer-applied `jenkins-verify` label is opt-in only and never substitutes for isolation.
- Keep CI separate from release/deployment. Do not deploy or change deployment configuration as part of verification.
- In review summaries, include the exact head SHA, required check result/source, Jenkins status when applicable, residual Actions work, and any unresolved verification limit.
