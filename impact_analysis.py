
import yaml
import json
import sys
from deepdiff import DeepDiff
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def build_mcp_prompt(changed_paths, impacted):
    prompt = {
        "role": "system",
        "content": "You are a software architecture assistant helping developers understand the impact of API changes."
    }
    user_input = {
        "changed_api_paths": list(changed_paths),
        "impacted_services": []
    }
    for dep in impacted:
        impacted_entry = {
            "service_name": dep['serviceName'],
            "affected_by": {
                "external_service": dep['externalCall']['service'],
                "path": dep['externalCall']['path'],
                "method": dep['externalCall']['method']
            },
            "impacted_endpoints": []
        }
        for origin in dep['originatingEndpoints']:
            impacted_entry["impacted_endpoints"].append({
                "path": origin['path'],
                "api": origin['api'],
                "internal_trace": origin['internalTrace']
            })
        user_input["impacted_services"].append(impacted_entry)

    return [prompt, {"role": "user", "content": json.dumps(user_input, indent=2)}]

def call_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=prompt,
        temperature=0.3
    )
    return response.choices[0].message.content

def main():
    old_spec = load_yaml(sys.argv[1])
    new_spec = load_yaml(sys.argv[2])
    dependencies = load_json(sys.argv[3])

    diff = DeepDiff(old_spec, new_spec, ignore_order=True)
    changed_paths = extract_changed_paths(diff)

    print("\U0001F50D Changed OpenAPI paths:")
    for p in sorted(changed_paths):
        print(f" - {p}")

    impacted = analyze_impact(changed_paths, dependencies)

    print("\n⚠️ Impacted Endpoints:")
    if not impacted:
        print(" - None")
    else:
        for dep in impacted:
            print("\n⚠️ Impacted Service:" + dep['serviceName'])
            for origin in dep['originatingEndpoints']:
                print(f" - {origin['api']} (via {' -> '.join(origin['internalTrace'])})")

        # 🧡 Generate MCP prompt and call OpenAI
        prompt = build_mcp_prompt(changed_paths, impacted)
        print("\n🧠 LLM Analysis:")
        print(call_openai(prompt))

if __name__ == "__main__":
    main()
