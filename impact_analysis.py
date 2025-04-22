import json
import sys
from pathlib import Path


def load_json(path):
    with open(path) as f:
        return json.load(f)


def find_impacts(deps, oas_diff):
    impacts = []

    paths_diff = oas_diff.get("pathsDiff", {})
    for dep in deps:
        call_path = dep["externalCall"]["path"]
        call_method = dep["externalCall"]["method"].upper()

        if call_path in paths_diff:
            methods_diff = paths_diff[call_path].get("methods", {})
            if call_method in methods_diff:
                method_changes = methods_diff[call_method]
                responses_diff = method_changes.get("responsesDiff", {})
                response_200 = responses_diff.get("200", {})
                schema_diff = response_200.get("contentDiff", {}).get("application/json", {}).get("schemaDiff", {})
                removed_fields = schema_diff.get("propertiesRemoved", {})

                for field in removed_fields:
                    impact = {
                        "externalService": dep["externalCall"].get("service", "unknown"),
                        "externalCall": {
                            "path": call_path,
                            "method": call_method
                        },
                        "change": "response_field_removed",
                        "field": field,
                        "impactedConsumers": dep.get("originatingEndpoints", [])
                    }
                    impacts.append(impact)

    return impacts


def main():
    if len(sys.argv) != 4:
        print("Usage: python impact_analysis.py <old_spec> <new_spec> <dependencies.json>")
        sys.exit(1)

    old_spec, new_spec, deps_file = sys.argv[1], sys.argv[2], sys.argv[3]

    # Run oasdiff
    diff_output_path = "openapi-diff.json"
    exit_code = os.system(f"oasdiff diff {old_spec} {new_spec} --format json > {diff_output_path}")
    if exit_code != 0:
        print("Failed to run oasdiff")
        sys.exit(1)

    deps = load_json(deps_file)
    oas_diff = load_json(diff_output_path)

    impacts = find_impacts(deps, oas_diff)
    print(json.dumps(impacts, indent=2))


if __name__ == "__main__":
    import os
    main()
