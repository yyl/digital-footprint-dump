# TODO

## Deferred Hardening

- Add OAuth `state` validation and stricter redirect URL verification to the Foursquare auth flow in `src/foursquare/api_client.py` to reduce CSRF/login-mixup risk during token bootstrap.
- Sanitize or allowlist outbound markdown link URLs in `src/publish/markdown_generator.py` so imported data cannot emit unsafe or malformed link targets into published reports.
- Refactor dependency injection to use explicit constructor arguments instead of "Poor Man's DI" (default instantiation like `self.db = db or RealDB()`). This will enforce safer testing by causing immediate failures if test cases forget to pass mock databases, rather than silently falling back to the real filesystem databases.
