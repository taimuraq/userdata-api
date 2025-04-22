import json
from deepdiff import DeepDiff

def compare_specs(old_spec_path, new_spec_path):
    # Load the old and new OpenAPI spec files
    with open(old_spec_path, 'r') as f:
        old_spec = json.load(f)

    with open(new_spec_path, 'r') as f:
        new_spec = json.load(f)

    # Use DeepDiff to compare the two OpenAPI spec files
    diff = DeepDiff(old_spec, new_spec, verbose_level=2)

    return diff

if __name__ == "__main__":
    old_spec_path = 'base-spec.json'   # Path to the old spec (can be fetched from previous commit)
    new_spec_path = 'openapi-spec.json'   # Path to the new spec

    differences = compare_specs(old_spec_path, new_spec_path)

    if differences:
        print("Differences found between old and new OpenAPI specs:", differences)
    else:
        print("No differences found.")
