# ============================================================
# auth.py
# ------------------------------------------------------------
# Purpose: Verify the Supabase JWT sent by the frontend on every
# request, and extract the real logged-in user's id from it.
#
# Supabase signs JWTs with either:
#   - HS256 (older projects)  → verify with the JWT secret string
#   - RS256 (newer projects)  → verify with the public key from JWKS
# We detect the algorithm from the token header and handle both.
# ============================================================

import os
import base64
import json
import jwt
import urllib.request
from functools import lru_cache
from fastapi import Header, HTTPException


def _decode_header(token: str) -> dict:
    """Decode the JWT header without verification (pure base64 decode)."""
    header_b64 = token.split(".")[0]
    # Pad to a multiple of 4
    header_b64 += "=" * (4 - len(header_b64) % 4)
    return json.loads(base64.b64decode(header_b64))


@lru_cache(maxsize=1)
def _get_jwks(jwks_uri: str) -> dict:
    """Fetch the JWKS (public keys) from Supabase once and cache the result."""
    with urllib.request.urlopen(jwks_uri, timeout=10) as resp:
        return json.loads(resp.read())


def get_current_user_id(authorization: str = Header(None)) -> str:
    """
    FastAPI dependency. Add `user_id: str = Depends(get_current_user_id)`
    to any route that should require login. Raises 401 if the token
    is missing, expired, or invalid.
    """
    secret = os.getenv("SUPABASE_JWT_SECRET")
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")

    if not authorization:
        print("[auth] 401 — no Authorization header received", flush=True)
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Are you logged in on the frontend?",
        )

    if not authorization.startswith("Bearer "):
        print(f"[auth] 401 — bad Authorization header: {authorization[:30]!r}", flush=True)
        raise HTTPException(
            status_code=401,
            detail=f"Invalid Authorization header format. Expected: Bearer <token>",
        )

    token = authorization.split(" ", 1)[1]

    # ── Detect algorithm from the token header ──────────────────────────────
    try:
        header = _decode_header(token)
    except Exception as e:
        print(f"[auth] 401 — cannot decode token header: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Malformed token header: {e}")

    alg = header.get("alg", "unknown")
    print(f"[auth] token algorithm: {alg}", flush=True)

    # ── Verify based on algorithm ───────────────────────────────────────────
    try:
        if alg == "HS256":
            # Older Supabase projects — symmetric secret
            if not secret:
                print("[auth] ERROR: SUPABASE_JWT_SECRET is not set (needed for HS256)", flush=True)
                raise HTTPException(
                    status_code=500,
                    detail="Server misconfigured: SUPABASE_JWT_SECRET is not set.",
                )
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )

        elif alg in ("RS256", "ES256"):
            # Newer Supabase projects — asymmetric keys via JWKS
            if not supabase_url:
                print("[auth] ERROR: SUPABASE_URL is not set (needed for RS256 JWKS fetch)", flush=True)
                raise HTTPException(
                    status_code=500,
                    detail="Server misconfigured: SUPABASE_URL is not set.",
                )
            jwks_uri = f"{supabase_url}/auth/v1/.well-known/jwks.json"
            print(f"[auth] fetching JWKS from {jwks_uri}", flush=True)
            try:
                jwks = _get_jwks(jwks_uri)
            except Exception as e:
                _get_jwks.cache_clear()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch JWKS from Supabase: {e}",
                )

            kid = header.get("kid")
            # Find the matching key by kid
            public_key = None
            for key_data in jwks.get("keys", []):
                if kid is None or key_data.get("kid") == kid:
                    kty = key_data.get("kty", "")
                    if kty == "EC":
                        public_key = jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(key_data))
                    else:
                        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_data))
                    break

            if public_key is None:
                print(f"[auth] 401 — no matching public key found in JWKS for kid={kid}", flush=True)
                raise HTTPException(status_code=401, detail=f"No matching public key found for kid={kid}.")

            payload = jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                audience="authenticated",
            )

        else:
            print(f"[auth] 401 — unsupported algorithm: {alg}", flush=True)
            raise HTTPException(status_code=401, detail=f"Unsupported JWT algorithm: {alg}")

    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        print("[auth] 401 — token is expired", flush=True)
        raise HTTPException(status_code=401, detail="Token expired. Please sign in again.")
    except jwt.InvalidAudienceError:
        try:
            raw = jwt.decode(token, options={"verify_signature": False})
            actual_aud = raw.get("aud")
        except Exception:
            actual_aud = "unknown"
        print(f"[auth] 401 — audience mismatch. Expected 'authenticated', got {actual_aud!r}", flush=True)
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token audience. Expected 'authenticated', got {actual_aud!r}.",
        )
    except jwt.InvalidTokenError as e:
        print(f"[auth] 401 — {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Invalid token: {type(e).__name__}: {e}")

    user_id = payload.get("sub")
    if not user_id:
        print("[auth] 401 — token has no 'sub' claim", flush=True)
        raise HTTPException(status_code=401, detail="Token missing 'sub' (user id) claim.")

    print(f"[auth] OK — user_id={user_id}", flush=True)
    return user_id
