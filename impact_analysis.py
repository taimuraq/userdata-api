import yaml
import json
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
        normalized = external_path.replace('{', '').replace('}', '')
        for changed in changed_paths:
            if changed.startswith(normalized) or normalized in changed:
                impacted.append(dep)
                break
    return impacted

def main():
    old_spec = load_yaml('tmp/old_spec.yaml')
    new_spec = load_yaml('tmp/new_spec.yaml')
    dependencies = load_json('tmp/dependencies.json')

    diff = DeepDiff(old_spec, new_spec, ignore_order=True)
    changed_paths = extract_changed_paths(diff)

    print("🔍 Changed OpenAPI paths:")
    for p in sorted(changed_paths):
        print(f" - {p}")

    impacted = analyze_impact(changed_paths, dependencies)
    print("\n⚠️ Impacted ShopperAPI Endpoints:")
    if not impacted:
        print(" - None")
    else:
        for dep in impacted:
            for origin in dep['originatingEndpoints']:
                print(f" - {origin['api']} (via {' -> '.join(origin['internalTrace'])})")

if __name__ == "__main__":
    main()
