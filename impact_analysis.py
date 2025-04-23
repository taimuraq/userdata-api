import yaml
import json
import sys
from deepdiff import DeepDiff

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def extract_changed_paths(diff):
    changed = set()
    for category in ['values_changed', 'dictionary_item_added', 'dictionary_item_removed']:
        for path in diff.get(category, {}):
            if path.startswith("root['paths']"):
                parts = path.split("'")
                if len(parts) >= 4:
                    changed.add(parts[3])
    return changed

def analyze_impact(changed_paths, dependencies):
    impacted = []
    for dep in dependencies:
        external_path = dep['externalCall']['path']
        for changed in changed_paths:
            if external_path in changed:
                impacted.append(dep)
                break
    return impacted

def main():
    old_spec = load_yaml(sys.argv[1])
    new_spec = load_yaml(sys.argv[2])
    dependencies = load_json(sys.argv[3])

    diff = DeepDiff(old_spec, new_spec, ignore_order=True)
    changed_paths = extract_changed_paths(diff)

    impacted = analyze_impact(changed_paths, dependencies)

    mcp_payload = {
        "context": {
            "sourceService": "userdata-api",
            "specChangedPaths": list(changed_paths),
            "dependenciesAnalyzed": "shopper-api"
        },
        "input": {
            "openapiDiffSummary": list(changed_paths),
            "dependencies": impacted
        },
        "instructions": [
            "Analyze if the changed paths in userdata-api could break any functionality in shopper-api.",
            "Provide suggestions for tests or validation needed in shopper-api if impacts exist.",
            "Highlight whether this change is safe or needs coordination across teams."
        ]
    }

    print(json.dumps(mcp_payload, indent=2))

if __name__ == "__main__":
    main()
