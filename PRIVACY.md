# Privacy notes

This is a plain description of how Bug Report AI handles data. It is written for a course project and is not legal advice. Before you use the software with real company data, have a qualified person review it.

## What is stored

- **Bug reports**: the title text, the project name, the severity and an id, in the `bug_reports` collection.
- **Predictions, duplicate suggestions and reviews**: the model's answers and what reviewers confirmed or corrected, with the id of the report they belong to.
- **Users**: name, email address, role, and a password **hash** (Argon2). The password itself is never stored.
- **Settings and model information**: the review margin, duplicate settings and model metrics.

## Where it is stored and who can see it

- Data is stored in the MongoDB Atlas database that you configure in `MONGODB_URI`. Atlas encrypts connections; check your own cluster settings for encryption at rest and backups.
- Signed-in users can see reports. Only admins can upload files, run bulk predictions, change settings, manage users and delete reports.

## Where data is sent

- The models (severity and duplicate search) run on your own server. Report text is **not** sent to any outside AI service.
- The "Try it" page and the "Evaluate" page do not save what you enter or upload.
- If you switch on the GitHub integration, the server reads the title of each new issue it receives from GitHub, and posts a label and a comment back to that issue using your token. Nothing else is sent to GitHub.
- The Hugging Face repository that holds the model files contains only the models, not your reports.

## Keeping and deleting data

- Data stays until it is deleted. Admins can delete a report; this also deletes its predictions, duplicate suggestions and reviews.
- A user can be deactivated from the Users page. Completely removing a user's record currently needs direct access to the database.
- `backend/backup_db.py` writes a backup file. Treat backup files like the data itself and delete them when they are no longer needed.

## Things to be careful about

- Bug reports can contain private information (customer names, internal addresses, passwords pasted by mistake). Do not upload data you are not allowed to share with the people who have access.
- The training data (public Bugzilla and Eclipse reports) is not private, but data you add later may be.
