# Plan for the last week

Tick each item when it is done. Keep the order: the earlier items protect the later ones.

## Day 1: put everything in and make it green
- [ ] Apply the final module, run the tests (backend, ML, frontend) and build the frontend.
- [ ] Commit, push, open a pull request, wait for the three green checks, merge, tag `v2.0`.
- [ ] Create `test_upload_500.csv` and `test_split_400.csv` (see `scripts/make_test_csv.py`).

## Day 2: measure the duplicate finder
- [ ] Label at least 100 pairs in `ml/data/labels/duplicate_pairs_to_label.csv` (about 1 hour), then run `python ml/src/evaluate_duplicates.py`.
- [ ] Review the pending duplicate suggestions in the app, then run `backend/duplicate_review_stats.py`.
- [ ] Write the numbers down. If the best threshold is not 0.80, change it in the Settings page.

## Day 3: put it online (or decide to demo locally)
- [ ] Follow `DEPLOY.md`: upload the model bundle, deploy the backend, deploy the frontend on Vercel.
- [ ] Run the checks at the end of `DEPLOY.md` (login, headers, `/docs` closed, wrong passwords lock the account).
- [ ] If the deployment is not working by the end of the day, stop. Use the local demo and a screen recording. A calm local demo is better than a broken live link.

## Day 4: the GitHub integration
- [ ] Follow `docs/GITHUB_INTEGRATION.md` with a test repository. Open three issues and look at the labels and comments.
- [ ] Take screenshots of the issue with its labels and comment.

## Day 5: write the report
- [ ] Problem, users, solution, data (and its limits), results (version 1 and 2, with the interval), the duplicate finder result, security and privacy, what is not done, next steps.
- [ ] Add screenshots: Try it, Upload, Bulk predict, Evaluate, Model performance, the GitHub issue.
- [ ] Use only numbers you have measured. Write the limits plainly; it makes the report stronger.

## Day 6: rehearse
- [ ] Practise the demo in `DEMO_SCRIPT.md` twice with a timer, and record one full run.
- [ ] Do a clean start test: restart the laptop, start the backend and the frontend, sign in.

## Day 7: buffer and submission
- [ ] Final `git pull`, run the tests once more, check the GitHub Actions page is green.
- [ ] Submit: the repository link (tags `v1.0` and `v2.0`), the report, the demo video, the live link (if it works) and the slides.
- [ ] Do not change code on the last day.

## What to put in the submission

| Item | Where |
| --- | --- |
| Source code | GitHub repository, tags `v1.0` and `v2.0` |
| Report | your document (PDF) |
| Demo video | a screen recording of the demo |
| Live link | only if it passed the checks |
| How to run it | `README.md` and `DEPLOY.md` |
| Honest limits | `README.md`, `PRIVACY.md`, `SECURITY.md` |

## About the dataset

Do not change the dataset for this submission. It has only short titles and every bug is marked fixed, which limits the model, but the limit is documented, the comparison between version 1 and version 2 is fair, and changing the data now would cost days with an uncertain gain. Present it as a known limit and a next step (add the full bug description, and train on a team's own labelled bugs).
