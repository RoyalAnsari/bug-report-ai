# Live demo script (about 7 minutes)

Before you start: backend and frontend are running, you are signed in as admin, the laptop is plugged in, and these are ready in a folder: `sample_data/test_upload_500.csv` (new reports) and `sample_data/test_split_400.csv` (honest test file). Also record a screen video of the whole demo once, as a backup in case the internet or the laptop fails.

| Time | What you do | What you say |
| --- | --- | --- |
| 0:00 | Slide or the Dashboard | "Teams get many bug reports every day. Deciding how urgent each one is takes time, and people report the same bug again and again. This tool suggests the severity, finds similar earlier bugs, and asks a person to check only the cases where the model is unsure." |
| 0:40 | **Try it**: click the example "Crash when saving a file with a very long name", press Analyse | "It suggests a severity, shows how sure it is, and lists similar earlier bugs. Nothing is saved." |
| 1:30 | Try "Typo in the preferences dialog", then a title with unclear wording to get **Needs review** | "When the model is not sure it says so. In our tests the predictions it does not flag are right 84% of the time, and the flagged ones only 48% of the time, so a person's time goes where it is needed." |
| 2:30 | **Upload** `test_upload_500.csv`, show the preview and the row errors if you used `--with-errors`, import | "A team can load its existing reports from a CSV." |
| 3:15 | **Bulk predict**: "Without a prediction" shows about 500. Set 100 per step, press Predict, show the progress bar | "It predicts them in small steps, so it works on a normal laptop. You can stop and continue." |
| 4:00 | Open one report, show the prediction, **Review**: confirm or correct | "The reviewer's answer is saved. This is how the model can later be trained on a team's own labels." |
| 4:30 | **Evaluate**: upload `test_split_400.csv` | "Any team can check the model on its own labelled bugs. Accuracy is 79%, but always guessing the most common class already gives about 81%, so we use macro F1 and look at each severity." |
| 5:15 | **Model performance**: version 1 and version 2 | "Version 1 (TF-IDF) had a macro F1 of 0.422. Version 2 (a fine-tuned transformer) has 0.449. The difference is small but real: the 95% interval is +0.009 to +0.047." |
| 5:45 | GitHub: create an issue in the test repository, wait a few seconds, show the label and comment | "This is how it fits into a developer's day: the label and the suggestions appear on the issue by themselves." |
| 6:30 | Limits and next steps | "It only sees the short title and was trained on public fixed bugs, so it is an assistant, not a decision maker. `major`, `minor` and `trivial` are still weak. Next: test with a real team's bugs, train on their labels, and connect Jira and Bugzilla." |

## If something goes wrong

- Backend not answering: show the recorded video, and say so.
- GitHub webhook does not fire: show the "Recent Deliveries" page, or use the recorded clip.
- A question you cannot answer: say "I do not know yet; here is how I would find out", then say how.

## Questions you may get

- **Why is the F1 only 0.45?** The data has only short titles, the labels are noisy (many bugs are left at the default `normal`), and the classes are very unbalanced. We report this openly instead of hiding it.
- **Why not just use accuracy?** 81% of the reports are `normal`, so guessing `normal` gives 81%. Macro F1 treats every severity equally.
- **Does it work for a company's own bugs?** Not proven. That is why the Evaluate page exists, and why the next step is a small trial with a real team.
- **Where does the data go?** The models run on your own server. Nothing is sent to an outside AI service.
