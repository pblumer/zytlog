from dataclasses import dataclass

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from backend.core.auth.keycloak import KeycloakClaims, extract_keycloak_claims


class TokenValidationError(Exception):
    pass


@dataclass
class JWTValidator:
    issuer: str
    jwks_url: str
    verify_audience: bool
    audience: str | None = None

    def __post_init__(self) -> None:
        self._jwks_client = PyJWKClient(self.jwks_url)

    def validate_token(self, token: str) -> KeycloakClaims:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token).key
            options = {"verify_aud": self.verify_audience}
            payload = jwt.decode(
                token,
                key=signing_key,
                algorithms=["RS256", "RS384", "RS512"],
                issuer=self.issuer,
                audience=self.audience if self.verify_audience else None,
                options=options,
            )
        except InvalidTokenError as exc:
            raise TokenValidationError("Invalid or expired token") from exc
        except Exception as exc:  # noqa: BLE001
            raise TokenValidationError("Unable to validate bearer token") from exc

        try:
            return extract_keycloak_claims(payload)
        except ValueError as exc:
            raise TokenValidationError("Invalid token payload") from exc
