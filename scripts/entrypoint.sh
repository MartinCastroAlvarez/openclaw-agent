#!/bin/sh
# 1) If GOOGLE_APPLICATION_CREDENTIALS_JSON is set, write to a separate file (google-credentials.json may be a read-only mount).
# 2) Ensure auth-profiles.json exists for google-vertex so the gateway finds the provider (ADC).
set -e
OPENCLAW="${HOME}/.openclaw"
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
  mkdir -p "$OPENCLAW"
  CRED_FILE="$OPENCLAW/google-credentials-from-env.json"
  printf '%s' "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > "$CRED_FILE"
  chmod 600 "$CRED_FILE"
  export GOOGLE_APPLICATION_CREDENTIALS="$CRED_FILE"
fi
# So "No API key found for provider google-vertex" is avoided: create auth profile for ADC when missing
AGENT_DIR="$OPENCLAW/agents/main/agent"
mkdir -p "$AGENT_DIR"
AUTH_PROFILES="$AGENT_DIR/auth-profiles.json"
if [ ! -f "$AUTH_PROFILES" ]; then
  printf '%s\n' '{"profiles":{"google-vertex:default":{"provider":"google-vertex","mode":"adc"}}}' > "$AUTH_PROFILES"
  chmod 600 "$AUTH_PROFILES"
fi
exec "$@"
