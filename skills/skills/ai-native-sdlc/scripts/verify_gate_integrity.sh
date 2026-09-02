#!/usr/bin/env bash
# verify_gate_integrity.sh — verify a downloaded ai-native-sdlc gate release.
#
# Run this BEFORE trusting a gate script with merge authority. Without verification you are
# taking on faith that the file deciding your merges is the one its authors published.
#
# Checks, in increasing strength:
#   1. SHA-256 matches the published digest        (detects corruption, not a determined attacker)
#   2. Sigstore signature is valid AND was made by this repo's release workflow
#   3. GitHub SLSA build provenance attestation is valid
#
# Check 1 alone is near-worthless against tampering: whoever replaces the artifact replaces
# the digest file next to it. Checks 2 and 3 are the ones that matter, because the identity
# is bound to a workflow in a named repository, not to a file an attacker controls.
#
# Usage:
#   verify_gate_integrity.sh <artifact.tar.gz> [--repo OWNER/REPO]
#
# Requires: cosign (https://github.com/sigstore/cosign) and gh (https://cli.github.com).
# Missing tools cause a hard failure, NOT a skip — a verification script that silently
# passes when it verified nothing is worse than no script.

set -euo pipefail

REPO="timwukp/agent-skills-best-practice"
WORKFLOW="release-attest.yml"
ARTIFACT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --workflow) WORKFLOW="$2"; shift 2 ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) ARTIFACT="$1"; shift ;;
  esac
done

if [ -z "$ARTIFACT" ]; then
  echo "usage: $(basename "$0") <artifact.tar.gz> [--repo OWNER/REPO]" >&2
  exit 2
fi
if [ ! -f "$ARTIFACT" ]; then
  echo "FAIL: no such file: $ARTIFACT" >&2
  exit 1
fi

fail() { echo "FAIL: $*" >&2; exit 1; }

echo "verifying: $ARTIFACT"
echo "expecting signer: https://github.com/$REPO/.github/workflows/$WORKFLOW@..."
echo

# --- 1. digest ---------------------------------------------------------------
if [ -f "$ARTIFACT.sha256" ]; then
  echo "[1/3] SHA-256"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c "$ARTIFACT.sha256" || fail "digest mismatch — the file is not what was published"
  else
    # macOS has shasum, not sha256sum.
    expected="$(cut -d' ' -f1 < "$ARTIFACT.sha256")"
    actual="$(shasum -a 256 "$ARTIFACT" | cut -d' ' -f1)"
    [ "$expected" = "$actual" ] || fail "digest mismatch — the file is not what was published"
    echo "  ok"
  fi
  echo "  note: this only detects corruption. An attacker who replaced the artifact also"
  echo "        replaced this digest file. Checks 2 and 3 are the real ones."
else
  echo "[1/3] SHA-256 — SKIPPED (no $ARTIFACT.sha256 alongside)"
fi
echo

# --- 2. signature ------------------------------------------------------------
echo "[2/3] Sigstore signature and signer identity"
command -v cosign >/dev/null 2>&1 || fail "cosign not installed — cannot verify the signature.
  Install: https://docs.sigstore.dev/cosign/system_config/installation/
  Refusing to report success on an unverified artifact."
[ -f "$ARTIFACT.sigstore.json" ] || fail "no signature bundle at $ARTIFACT.sigstore.json"

# The identity regexp pins BOTH the repository and the specific workflow file. Verifying
# only that "some Sigstore signature exists" would accept a signature from any GitHub
# workflow anywhere, which proves nothing.
cosign verify-blob "$ARTIFACT" \
  --bundle "$ARTIFACT.sigstore.json" \
  --certificate-identity-regexp "^https://github\.com/${REPO//\//\\/}/\.github/workflows/${WORKFLOW//./\\.}@" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  || fail "signature verification failed — do not use this artifact"
echo "  ok — signed by the expected workflow in the expected repository"
echo

# --- 3. provenance -----------------------------------------------------------
echo "[3/3] SLSA build provenance"
if command -v gh >/dev/null 2>&1; then
  gh attestation verify "$ARTIFACT" --repo "$REPO" \
    || fail "provenance verification failed — do not use this artifact"
  echo "  ok"
  echo "  note: GitHub attestations alone are SLSA Build Level 2. For Level 3 assurance add"
  echo "        --signer-workflow $REPO/.github/workflows/$WORKFLOW"
else
  echo "  SKIPPED — gh not installed (https://cli.github.com)"
  echo "  Signature check above already binds the artifact to the release workflow."
fi
echo

echo "VERIFIED: $ARTIFACT"
echo
echo "Verification proves origin and integrity. It does NOT prove the gate is correct,"
echo "well-designed, or adequate for your compliance regime. Read references/limitations.md."
