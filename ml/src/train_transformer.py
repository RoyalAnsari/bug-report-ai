"""Severity ke liye transformer (DistilBERT) fine-tune karta hai aur TF-IDF model se mawazna ke liye numbers deta hai.

Yeh GPU wale computer par chalane ke liye hai (Google Colab ya Kaggle muft GPU deta hai). 8 GB wale CPU laptop par
yeh ghanton lega, is liye script CPU par bina --allow-cpu ke chalne se inkaar karti hai.

Tareeqa wahi hai jo TF-IDF model ka tha, taake mawazna insaaf par ho:
  - wahi train / val / test files (ml/data/processed), test sirf aakhir mein ek baar naapa jata hai,
  - class weights (resampling nahi, kyunke woh pehle kaam nahi aaya),
  - validation par har class ke score mein "offset" tune hota hai (macro F1 ke liye),
  - wahi 6 classes aur wahi metrics.json ki shakl.

Chalane ka tareeqa (Colab mein, train.csv, val.csv, test.csv aur yeh file upload karke):
  python train_transformer.py --data-dir /content --out-dir /content/severity_transformer --limit 400 --epochs 1   (jaanch)
  python train_transformer.py --data-dir /content --out-dir /content/severity_transformer                          (asli)
"""
import argparse
import json
import platform
import random
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# metrics.json ke labels_order jaisi hi tarteeb.
LABELS = ["blocker", "critical", "major", "normal", "minor", "trivial"]


def build_input_text(text, project):
    text = " ".join(str(text).split())
    name = str(project or "unknown").strip().lower().replace(" ", "_")
    return f"{name}: {text}"


def class_weights(counts, power=0.5):
    """Kam wali classes ko zyada weight. power=1 poora 'balanced' hai, 0.5 naram (sqrt) hai."""
    counts = np.asarray(counts, dtype=np.float64)
    if (counts <= 0).any():
        raise ValueError("Har class ki kam se kam ek misaal honi chahiye")
    raw = (counts.sum() / (len(counts) * counts)) ** power
    return raw / raw.mean()


def macro_f1(y_true, y_pred):
    from sklearn.metrics import f1_score

    return float(f1_score(y_true, y_pred, labels=list(range(len(LABELS))), average="macro", zero_division=0))


def tune_offsets(logits, y_true, sweeps=2, grid=None):
    """Validation par har class ke score mein chhota sa izafa/kami dhoondhta hai jis se macro F1 sab se zyada ho."""
    grid = np.round(np.arange(-2.0, 2.0001, 0.1), 2) if grid is None else grid
    offsets = np.zeros(logits.shape[1], dtype=np.float64)
    best = macro_f1(y_true, (logits + offsets).argmax(axis=1))
    for _ in range(sweeps):
        for k in range(logits.shape[1]):
            for value in grid:
                trial = offsets.copy()
                trial[k] = value
                score = macro_f1(y_true, (logits + trial).argmax(axis=1))
                if score > best + 1e-9:
                    best, offsets = score, trial
    return offsets, best


def load_split(directory, name, limit, seed):
    frame = pd.read_csv(Path(directory) / f"{name}.csv", encoding="utf-8")
    missing = {"project", "severity", "text"} - set(frame.columns)
    if missing:
        raise SystemExit(f"{name}.csv mein yeh columns nahi hain: {sorted(missing)}")
    unknown = set(frame["severity"].unique()) - set(LABELS)
    if unknown:
        raise SystemExit(f"{name}.csv mein anjaan severity labels hain: {sorted(unknown)}")
    if limit and len(frame) > limit:
        frame = frame.sample(n=limit, random_state=seed).reset_index(drop=True)
    texts = [build_input_text(t, p) for t, p in zip(frame["text"], frame["project"])]
    labels = frame["severity"].map({label: index for index, label in enumerate(LABELS)}).to_numpy(dtype=np.int64)
    return texts, labels


def encode(tokenizer, texts, max_len):
    encoded = tokenizer(texts, truncation=True, max_length=max_len)
    return [
        {"input_ids": ids, "attention_mask": mask}
        for ids, mask in zip(encoded["input_ids"], encoded["attention_mask"])
    ]


def make_batch(tokenizer, features, device):
    batch = tokenizer.pad(features, padding=True, return_tensors="pt")
    return {key: value.to(device) for key, value in batch.items()}


def predict_logits(model, tokenizer, features, device, batch_size, torch):
    order = np.argsort([len(item["input_ids"]) for item in features])
    logits = np.zeros((len(features), len(LABELS)), dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for start in range(0, len(features), batch_size):
            indexes = order[start:start + batch_size]
            batch = make_batch(tokenizer, [features[i] for i in indexes], device)
            logits[indexes] = model(**batch).logits.float().cpu().numpy()
    return logits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="ml/data/processed")
    parser.add_argument("--out-dir", default="ml/artifacts/severity_transformer")
    parser.add_argument("--model-name", default="distilbert-base-uncased")
    parser.add_argument("--max-len", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--class-weight-power", type=float, default=0.5)
    parser.add_argument("--patience", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=0, help="jaanch ke liye har file se itni hi rows (0 = sab)")
    parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args()

    import torch
    import transformers
    from sklearn.metrics import classification_report, confusion_matrix
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cpu" and not args.allow_cpu:
        raise SystemExit("GPU nahi mila. Colab/Kaggle par GPU chalayein (CPU par bohat der lagegi). Phir bhi chalana ho to --allow-cpu dein.")
    use_amp = device.type == "cuda"

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    started = time.time()
    train_texts, y_train = load_split(args.data_dir, "train", args.limit, args.seed)
    val_texts, y_val = load_split(args.data_dir, "val", args.limit, args.seed)
    test_texts, y_test = load_split(args.data_dir, "test", args.limit, args.seed)
    print(f"Rows: train {len(y_train)}, val {len(y_val)}, test {len(y_test)}   device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    train_features = encode(tokenizer, train_texts, args.max_len)
    val_features = encode(tokenizer, val_texts, args.max_len)
    test_features = encode(tokenizer, test_texts, args.max_len)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(LABELS),
        id2label={index: name for index, name in enumerate(LABELS)},
        label2id={name: index for index, name in enumerate(LABELS)},
    ).to(device)

    # --limit wali chhoti jaanch mein koi class chhoot sakti hai, is liye ginti kam se kam 1 rakhte hain.
    counts = np.maximum(np.bincount(y_train, minlength=len(LABELS)), 1)
    weights = class_weights(counts, args.class_weight_power)
    print("Class weights:", {name: round(float(w), 2) for name, w in zip(LABELS, weights)})
    loss_fn = torch.nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))

    steps_per_epoch = int(np.ceil(len(y_train) / args.batch_size))
    total_steps = steps_per_epoch * args.epochs
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.06 * total_steps), total_steps)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    rng = np.random.RandomState(args.seed)
    best_f1, best_epoch, best_state, waited = -1.0, 0, None, 0
    epoch_results = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        permutation = rng.permutation(len(y_train))
        running = 0.0
        for step, start in enumerate(range(0, len(y_train), args.batch_size), start=1):
            indexes = permutation[start:start + args.batch_size]
            batch = make_batch(tokenizer, [train_features[i] for i in indexes], device)
            labels = torch.tensor(y_train[indexes], device=device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
                outputs = model(**batch)
            loss = loss_fn(outputs.logits.float(), labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            running += float(loss.item())
            if step % 200 == 0:
                print(f"  epoch {epoch} step {step}/{steps_per_epoch} loss {running / 200:.4f}")
                running = 0.0

        val_logits = predict_logits(model, tokenizer, val_features, device, 128, torch)
        val_f1 = macro_f1(y_val, val_logits.argmax(axis=1))
        epoch_results.append({"epoch": epoch, "val_macro_f1": round(val_f1, 4)})
        print(f"Epoch {epoch}: validation macro F1 = {val_f1:.4f}  ({(time.time() - started) / 60:.1f} min)")
        if val_f1 > best_f1:
            best_f1, best_epoch, waited = val_f1, epoch, 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            waited += 1
            if waited >= args.patience:
                print("Validation F1 nahi barha, training ruk gayi.")
                break

    model.load_state_dict(best_state)
    val_logits = predict_logits(model, tokenizer, val_features, device, 128, torch)
    offsets, val_f1_offsets = tune_offsets(val_logits, y_val)
    val_f1_plain = macro_f1(y_val, val_logits.argmax(axis=1))
    print(f"Validation macro F1: {val_f1_plain:.4f} (offsets ke baghair), {val_f1_offsets:.4f} (offsets ke saath)")

    # Test sirf ab, ek baar.
    test_logits = predict_logits(model, tokenizer, test_features, device, 128, torch)
    test_pred = (test_logits + offsets).argmax(axis=1)
    test_f1 = macro_f1(y_test, test_pred)
    test_f1_plain = macro_f1(y_test, test_logits.argmax(axis=1))
    print(f"TEST macro F1: {test_f1:.4f} (offsets ke saath), {test_f1_plain:.4f} (offsets ke baghair)")
    report = classification_report(
        y_test, test_pred, labels=list(range(len(LABELS))), target_names=LABELS, output_dict=True, zero_division=0
    )
    matrix = confusion_matrix(y_test, test_pred, labels=list(range(len(LABELS))))
    for name in LABELS:
        print(f"  {name:9s} f1 {report[name]['f1-score']:.3f}  precision {report[name]['precision']:.3f}  recall {report[name]['recall']:.3f}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out_dir / "model")
    tokenizer.save_pretrained(out_dir / "model")
    (out_dir / "labels.json").write_text(json.dumps(LABELS), encoding="utf-8")
    (out_dir / "offsets.json").write_text(json.dumps([float(x) for x in offsets]), encoding="utf-8")
    np.save(out_dir / "val_logits.npy", val_logits)
    np.save(out_dir / "test_logits.npy", test_logits)
    np.save(out_dir / "val_labels.npy", y_val)
    np.save(out_dir / "test_labels.npy", y_test)

    metrics = {
        "chosen": {
            "variant": f"transformer_{args.model_name.split('/')[-1]}",
            "offsets": True,
            "val_macro_f1": val_f1_offsets,
            "offset_values": [float(x) for x in offsets],
        },
        "all_validation_results": [
            {"variant": "transformer", "offsets": False, "val_macro_f1": val_f1_plain},
            {"variant": "transformer", "offsets": True, "val_macro_f1": val_f1_offsets},
        ],
        "epochs": epoch_results,
        "test": {
            "macro_f1": test_f1,
            "per_class": report,
            "confusion_matrix": matrix.tolist(),
            "labels_order": LABELS,
            "rows": int(len(y_test)),
        },
        "test_without_offsets": {"macro_f1": test_f1_plain},
        "training": {
            "model_name": args.model_name,
            "best_epoch": best_epoch,
            "max_len": args.max_len,
            "learning_rate": args.lr,
            "batch_size": args.batch_size,
            "class_weight_power": args.class_weight_power,
            "seed": args.seed,
            "device": str(device),
            "rows_limit": args.limit,
            "minutes": round((time.time() - started) / 60, 1),
        },
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    archive = shutil.make_archive(str(out_dir), "zip", out_dir)
    print(f"\nSab kuch save hua: {out_dir}\nZip (download ke liye): {archive}")


if __name__ == "__main__":
    sys.exit(main())
