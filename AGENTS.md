# CI and pull-request verification

Repository: `setnessconsulting/game-ai-playtest-lab`
Adoption state: `Jenkins authoritative`
Authoritative PR check(s): `jenkins-pr-gate`
Jenkins check(s): `jenkins-pr-gate`, published by the `setness-jenkins-ci` GitHub App (App ID `5043075`)
Jenkins-supported triggers/lanes: pull request for open, non-draft, same-repository PRs authored by `setnessconsulting` or by verified same-repository Dependabot (bot identity and branch prefix, enforced by the trusted planner)
Owner-controlled Actions fallback: `.github/workflows/jenkins-fallback.yml` (manual `workflow_dispatch`, owner-controlled, exact-SHA)
Fork PR support: `not qualified`
Fork opt-in label: `jenkins-verify` (maintainer-only; the label alone does not enable execution)
Deployment boundary: Jenkins performs no deployment for this repository; release and deployment remain outside Jenkins.

- Before authoring or reviewing a pull request, refresh the current PR head SHA, live check statuses and sources, and branch-protection requirements. State which system is authoritative for this repository.
- Jenkins is authoritative here. Require `jenkins-pr-gate` to be complete on the exact current PR head SHA and attributed to App ID `5043075`. Ignore stale results and results from a different source.
- `.github/workflows/ci.yml` is manual-only for owner-requested verification. The exact-SHA owner fallback also remains manual-only. Routine pushes do not run Actions, and neither workflow is the PR gate.
- Do not start routine GitHub Actions verification. Use only the documented owner-controlled fallback when needed, and say which SHA it tested and why it was invoked.
- Never run a pull-request-supplied Jenkinsfile. Never expose the GitHub App private key, Checks-write credential, production secret, controller data, Docker socket, or persistent agent state to repository code.
- Fork verification stays disabled until the per-run untrusted sandbox is qualified. A maintainer-applied `jenkins-verify` label is opt-in only and never substitutes for isolation.
- Keep CI separate from release/deployment. Do not deploy or change deployment configuration as part of verification.
- In review summaries, include the exact head SHA, required check result/source, Jenkins status when applicable, residual Actions work, and any unresolved verification limit.
