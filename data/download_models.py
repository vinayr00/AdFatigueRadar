import os
import sys
import time
from huggingface_hub import snapshot_download

models = [
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "cardiffnlp/twitter-roberta-base-irony",
    "cardiffnlp/twitter-xlm-roberta-base-sentiment"
]

base_dir = r"d:\kaladharroyal\projects\AdFatigue\data\models"
os.makedirs(base_dir, exist_ok=True)

for repo_id in models:
    folder_name = repo_id.split("/")[-1]
    target_dir = os.path.join(base_dir, folder_name)
    print(f"\n=======================================================")
    print(f"Downloading {repo_id} -> {target_dir}")
    print(f"=======================================================")
    
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            snapshot_download(
                repo_id=repo_id,
                local_dir=target_dir,
                resume_download=True,
                max_workers=2
            )
            print(f"[SUCCESS] Downloaded {repo_id} to {target_dir}")
            break
        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Error downloading {repo_id}: {e}", file=sys.stderr)
            if attempt < max_retries:
                time.sleep(3)
            else:
                print(f"[FAILED] Failed to download {repo_id} after {max_retries} attempts.", file=sys.stderr)

print("\nAll tasks finished!")
