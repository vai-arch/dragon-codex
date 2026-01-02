import sys
import traceback
from datetime import datetime

import numpy as np
import torch
from datasets import DatasetDict, load_dataset
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import MultiLabelBinarizer
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_statistics import total_statistics_logging

in_file_query_classification_training = None
out_query_classifier_model_path = None
cfg_query_model_training = None
labels = None


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = torch.sigmoid(torch.tensor(logits)).numpy()
    preds = (probs > 0.5).astype(int)
    f1 = f1_score(labels, preds, average="macro")
    acc = accuracy_score(labels, preds)
    return {"eval_f1_macro": f1, "eval_accuracy": acc}


def main():
    start_time = datetime.now()
    statistics = {}

    cfg = cfg_query_model_training

    # Load dataset
    dataset = load_dataset("json", data_files=str(in_file_query_classification_training))

    # Multi-label binarizer
    mlb = MultiLabelBinarizer(classes=labels)
    mlb.fit([labels])

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(cfg["MODEL_NAME"])

    def preprocess_function(examples):
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=cfg["MAX_LENGTH"],
        )
        binary_labels = mlb.transform(examples["categories"])
        tokenized["labels"] = binary_labels.astype(np.float32).tolist()
        return tokenized

    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    # Split
    train_test = tokenized_dataset["train"].train_test_split(test_size=cfg["TEST_SIZE"], seed=cfg["SEED"])
    dataset_dict = DatasetDict(
        {
            "train": train_test["train"],
            "validation": train_test["test"],
        }
    )

    # Model - with correct label count
    num_labels = len(labels)
    model = AutoModelForSequenceClassification.from_pretrained(
        cfg["MODEL_NAME"],
        num_labels=num_labels,
        problem_type="multi_label_classification",
    )

    # === CRITICAL: Set label mappings BEFORE training/saving ===
    model.config.id2label = {i: label for i, label in enumerate(labels)}
    model.config.label2id = {label: i for i, label in enumerate(labels)}

    # Training arguments - fully driven by QUERY_MODEL_TRAINING config
    training_args = TrainingArguments(
        output_dir=out_query_classifier_model_path,
        eval_strategy=cfg["EVAL_STRATEGY"],  # "no" on CPU, "epoch" on GPU
        save_strategy="epoch",
        logging_strategy="epoch",
        num_train_epochs=cfg["NUM_EPOCHS"],
        per_device_train_batch_size=cfg["TRAIN_BATCH_SIZE"],
        per_device_eval_batch_size=cfg["EVAL_BATCH_SIZE"],
        warmup_steps=cfg["WARMUP_STEPS"],
        weight_decay=cfg["WEIGHT_DECAY"],
        learning_rate=cfg["LEARNING_RATE"],
        load_best_model_at_end=cfg.get("LOAD_BEST_MODEL_AT_END", False),
        metric_for_best_model=cfg.get("METRIC_FOR_BEST_MODEL", None),
        greater_is_better=True,  # Only used if evaluation enabled
        save_total_limit=cfg["SAVE_TOTAL_LIMIT"],
        report_to=[],
        fp16=cfg["FP16"],  # True on GPU, False on CPU
        seed=cfg["SEED"],
        dataloader_pin_memory=False,  # Avoids CPU warning
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset_dict["train"],
        eval_dataset=dataset_dict["validation"],
        compute_metrics=compute_metrics,
    )

    # Train
    trainer.train()

    # === Save model with correct labels baked in ===
    trainer.save_model(out_query_classifier_model_path)
    tokenizer.save_pretrained(out_query_classifier_model_path)

    # Final evaluation for stats
    final_metrics = trainer.evaluate()
    best_metric = trainer.state.best_metric or final_metrics["eval_f1_macro"]

    # Statistics
    statistics = {
        "name": "wot_query_classifier",
        "timestamp": datetime.now().isoformat(),
        "config": cfg,
        "dataset": {
            "total_examples": len(dataset["train"]),
            "train_examples": len(dataset_dict["train"]),
            "validation_examples": len(dataset_dict["validation"]),
        },
        "training": {
            "epochs_trained": trainer.state.epoch or cfg["NUM_EPOCHS"],
            "total_steps": trainer.state.global_step,
        },
        "metrics": {
            "best_eval_f1_macro": best_metric,
            "final_eval_f1_macro": final_metrics["eval_f1_macro"],
            "final_eval_accuracy": final_metrics["eval_accuracy"],
            "final_eval_loss": final_metrics["eval_loss"],
        },
    }

    print(f"Training complete. Model saved to {out_query_classifier_model_path}")
    print(f"Best validation F1_macro: {best_metric:.4f}")

    total_time = datetime.now() - start_time
    total_statistics_logging(
        log_name="wot_query_classifier",
        statistics=statistics,
        tables=False,
        title="QUERY CLASSIFIER TRAINING",
        total_time=total_time,
    )


if __name__ == "__main__":
    # Initialize paths from config
    paths = get_paths()
    config = get_config()

    # Input paths - embedding files
    in_file_query_classification_training = paths.FILE_QUERY_CLASSIFIER_MODEL_TRAINING_DATA

    # Output paths - Query classifier model collections
    out_query_classifier_model_path = paths.QUERY_CLASSIFIER_MODEL_PATH

    cfg_query_model_training = config.QUERY_MODEL_TRAINING
    labels = cfg_query_model_training["LABELS"]

    try:
        main()
        exit_code = 0
    except Exception as e:
        print(f"\n❌ An error occurred in the script: {str(e)}")
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
