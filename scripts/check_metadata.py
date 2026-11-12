from pathlib import Path
import yaml
import sys
sys.path.insert(0, "murmel")
from wyoming_murmel.__main__ import validate
from wyoming_murmel import __version__

config = yaml.safe_load(Path("murmel/config.yaml").read_text())
assert config["version"] == __version__
assert config["arch"] == ["amd64"]
assert config["discovery"] == ["wyoming"]
assert config["ports"]["10300/tcp"] is None
validate(config["options"])
for language in ("nl", "en"):
    labels = yaml.safe_load(Path(f"murmel/translations/{language}.yaml").read_text())
    assert set(labels["configuration"]) == set(config["schema"])
print("Metadata OK")
