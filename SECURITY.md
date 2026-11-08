# Security

## Reporting a problem

If you find a security problem, please do not open a public issue. Use the repository's **Security** tab and choose "Report a vulnerability" (a private GitHub security advisory), and describe what you found and how to reproduce it.

## What is in place

- Passwords are hashed with Argon2. Login tokens are signed and expire. Changing a password signs that user out everywhere.
- Two roles (admin and reviewer), checked on the server for every request.
- An account is locked for a while after repeated wrong passwords.
- Security headers on every response, strict CORS, and the API documentation pages are off by default.
- The GitHub webhook only accepts requests with a valid signature.
- Secrets live in environment variables (`backend/.env`, never in Git). Dependency checks (`pip-audit`, `npm audit`) run in GitHub Actions.

## What is not done

- No independent security review or penetration test has been done.
- No two-factor login, no email-based password reset and no per-user data separation (all users see the same reports).
- No rate limiting by IP address inside the application. Add it at the host or reverse proxy.
- Login tokens cannot be revoked one by one, and they are kept in the browser tab's session storage.
- Backups, monitoring and alerts depend on the hosting you choose.

## Good practice when you run it

- Use a long random `JWT_SECRET` and a strong database password, and rotate them if they were ever shown or committed.
- Keep `AUTH_ENABLED=true` and `ENABLE_DOCS=false` outside local development.
- Give the GitHub token only the permission it needs (Issues: read and write on one repository).
