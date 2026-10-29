"""Render images without third-party dependencies. Namespace is bootstrapped by admin."""
import os
from pathlib import Path
root = Path(__file__).resolve().parents[1]
registry = os.environ["ECR_REGISTRY"]
tag = os.environ["IMAGE_TAG"]
text = (root / "k8s/base.yaml").read_text()
# Admin creates the Namespace; the deploy role has namespace-only permissions.
text = text.split("---\n", 1)[1]
for service in ("tasks", "summary", "frontend"):
    text = text.replace(f"launchpad-{service}:local", f"{registry}/launchpad-{service}:{tag}")
print(text, end="")
