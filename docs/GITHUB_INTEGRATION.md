# Using Bug Report AI with GitHub

When someone opens a new issue, the backend reads its title and does three things:

1. adds a label such as `severity: major`,
2. adds `triage: needs review` when the model is not sure, and `triage: possible duplicate` when it finds a very similar earlier bug,
3. writes one comment with the suggested severity and the similar earlier bugs. The comment says it is a suggestion for a person to confirm.

Only issues that are **opened** are handled (not edits, closes or pull requests).

## Set it up (about 10 minutes)

1. **A repository to test with.** Create a new repository (a private one is fine) or use an existing one.
2. **A token.** On GitHub open Settings, Developer settings, Personal access tokens, Fine-grained tokens, Generate new token. Under "Repository access" choose **Only select repositories** and pick the test repository. Under "Repository permissions" set **Issues** to **Read and write**. Copy the token once; GitHub does not show it again.
3. **A secret.** Make up a random text of at least 16 characters, for example with `python -c "import secrets; print(secrets.token_urlsafe(24))"`.
4. **Put both in the backend settings** (`backend/.env` on your computer, or the host's environment variables when deployed), then restart the backend:

   ```
   GITHUB_WEBHOOK_SECRET=the secret from step 3
   GITHUB_TOKEN=the token from step 2
   ```

5. **Give the backend a public address.** GitHub must be able to reach it.
   - Deployed backend: use its address, for example `https://your-backend.example.com`.
   - Running on your own computer: start a tunnel, for example `ngrok http 8000` or `cloudflared tunnel --url http://localhost:8000`, and use the https address it prints. The address changes each time you start the tunnel, so update the webhook then.
6. **Add the webhook.** In the repository open Settings, Webhooks, Add webhook:
   - Payload URL: `https://YOUR-ADDRESS/api/v1/integrations/github/webhook`
   - Content type: `application/json`
   - Secret: the secret from step 3
   - Events: "Let me select individual events", then tick only **Issues**.
7. **Try it.** Open a new issue, for example "Crash when saving a file with a very long name". After a few seconds the labels and the comment appear.

## If nothing happens

Open the webhook page, "Recent Deliveries", and click the latest delivery.

| What you see | Meaning |
| --- | --- |
| 404 | The secret is not set in the backend, or the address is wrong. |
| 401 | The secret in GitHub and in the backend are different. |
| 202 but no label | Look at the backend log. "GitHub issue skipped" means the model is not loaded or `GITHUB_TOKEN` is missing. An error from GitHub (403 or 404) usually means the token does not have Issues write permission for that repository. |
| Timeout | The backend or the tunnel is not running. |

## Safety

- Only requests signed with your secret are accepted.
- Use a token limited to one repository and remove it (and the webhook) after a demo.
- The same idea works for Jira or Bugzilla, but only GitHub is built.
