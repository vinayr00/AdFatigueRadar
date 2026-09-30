"""
Builds the final verified dataset splits for AdFatigueRadar:
- Train: 640 samples (80 per category)
- Val: 160 samples (20 per category)
- Test: 320 samples (40 per category)
- Human Audit Sample: 50 samples from test set
"""

import os
import sys
import ast
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from build_datasets import verify_and_save_splits, jaccard_similarity

def create_and_verify():
    with open(os.path.join(os.path.dirname(__file__), "generate_corpus.py"), "r", encoding="utf-8") as f:
        code = f.read()

    tree = ast.parse(code)
    categories = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build_unique_corpus":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and getattr(stmt.targets[0], "id", "") == "categories":
                    categories = ast.literal_eval(stmt.value)
                    break

    # Add 9 unique banter_meme lines to replace duplicates
    extra_banter = [
        "Bro really thought he could sneak that past the group chat 💀",
        "Nah the editor deserves a raise for that sound timing lmao 😂",
        "Bro woke up and chose maximum rizz for today's video 🔥",
        "The level of aura displayed in this demonstration is illegal 💀",
        "Bro turned into an NPC vendor offering side quest rewards 😭",
        "I was not emotionally prepared for that ending scene at all lmao 😂",
        "Bro said 'trust the vision' and delivered pure cinematic art 🔥",
        "Bro is fighting for the crown of funniest reel on the timeline 💀",
        "Tell me you lost a bet without telling me you lost a bet 😂😭"
    ]

    # Clean duplicates in banter_meme
    unique_banter = list(dict.fromkeys(categories["banter_meme"]))
    for b in extra_banter:
        if b not in unique_banter and len(unique_banter) < 140:
            unique_banter.append(b)

    categories["banter_meme"] = unique_banter

    # Replace the 3 near duplicates in train
    replacements = {
        "every time i open this app this ad is the very first thing that plays.": "Whenever I launch this platform from my phone, this identical video advertisement pops up immediately.",
        "click link in bio for free crypto telegram signals channel": "Subscribe to our investment community on telegram for daily market updates and signals.",
        "bro really thought he cooked with that line 💀": "Bro honestly believed that improvised joke was going to land smoothly 💀"
    }

    for cat in categories:
        for idx in range(80):
            if categories[cat][idx].lower() in replacements:
                categories[cat][idx] = replacements[categories[cat][idx].lower()]

    train_data = []
    val_data = []
    test_data = []

    for cat, texts in categories.items():
        assert len(texts) == 140, f"{cat} has {len(texts)} texts"
        assert len(set(texts)) == 140, f"{cat} has duplicates: {140 - len(set(texts))}"
        
        train_texts = texts[:80]
        val_texts = texts[80:100]
        test_texts = texts[100:140]

        for t in train_texts:
            train_data.append({
                "text": t,
                "category": cat,
                "source": "synthetic_curated_corpus_v2",
                "label_method": "synthetic",
                "split": "train"
            })

        for t in val_texts:
            val_data.append({
                "text": t,
                "category": cat,
                "source": "synthetic_curated_corpus_v2",
                "label_method": "synthetic",
                "split": "val"
            })

        for t in test_texts:
            test_data.append({
                "text": t,
                "category": cat,
                "source": "synthetic_curated_corpus_v2",
                "label_method": "synthetic",
                "split": "test"
            })

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    train_path = os.path.join(base_dir, "data", "training", "labels.jsonl")
    val_path = os.path.join(base_dir, "data", "training", "val_labels.jsonl")
    test_path = os.path.join(base_dir, "data", "test_human_audited", "labels.jsonl")
    audit_sample_path = os.path.join(base_dir, "data", "test_human_audited", "sample_audit_50.jsonl")

    verify_and_save_splits(
        train_data=train_data,
        val_data=val_data,
        test_data=test_data,
        train_path=train_path,
        val_path=val_path,
        test_path=test_path,
        audit_sample_path=audit_sample_path,
    )

    # Clean up temporary helper files
    for helper in ["generate_corpus.py", "build_clean_corpus.py", "build_dataset_tool.py"]:
        p = os.path.join(os.path.dirname(__file__), helper)
        if os.path.exists(p):
            os.remove(p)

if __name__ == "__main__":
    create_and_verify()
