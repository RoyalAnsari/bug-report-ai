SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

# API sirf JSON deti hai, is liye koi script, style ya frame nahi chahiye.
API_CSP = "default-src 'none'; frame-ancestors 'none'"

HSTS = "max-age=31536000; includeSubDomains"

# Swagger UI ko apni scripts chahiye, is liye in raaston par CSP nahi lagti.
DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")


def apply_security_headers(headers, path, enable_hsts=False):
    """Response mein security headers jodta hai (pehle se maujood header ko nahi badalta)."""
    for name, value in SECURITY_HEADERS.items():
        headers.setdefault(name, value)
    if not path.startswith(DOCS_PREFIXES):
        headers.setdefault("Content-Security-Policy", API_CSP)
    if path.startswith("/api/"):
        headers.setdefault("Cache-Control", "no-store")
    if enable_hsts:
        headers.setdefault("Strict-Transport-Security", HSTS)
