# TODO

## Deferred Hardening

- Add OAuth `state` validation and stricter redirect URL verification to the Foursquare auth flow in `src/foursquare/api_client.py` to reduce CSRF/login-mixup risk during token bootstrap.
- Sanitize or allowlist outbound markdown link URLs in `src/publish/markdown_generator.py` so imported data cannot emit unsafe or malformed link targets into published reports.
