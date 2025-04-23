
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

    output_string = "\U0001F50D Changed OpenAPI paths:\n"

    #print("\U0001F50D Changed OpenAPI paths:")
    for p in sorted(changed_paths):
        output_string += (f" - {p}")

    impacted = analyze_impact(changed_paths, dependencies)

    # Start building the string for the output
    #output_string += "\n⚠️ Impacted Endpoints:\n"

    if not impacted:
        output_string += " - None\n"
    else:
        for dep in impacted:
            output_string += f"\n⚠️ Impacted Service: {dep['serviceName']}\n"
            for origin in dep['originatingEndpoints']:
                output_string += f" - {origin['api']} (via {' -> '.join(origin['internalTrace'])})\n"

        #print(output_string)
        # 🧡 Generate MCP prompt and call OpenAI
        prompt = build_mcp_prompt(changed_paths, impacted)
        print("\n🧠 LLM Analysis:")
        analysis = output_string + "\n" ""+ call_openai(prompt)
        #analysis = "call_openai(prompt)"
        print(analysis)

        # ✍️ Write analysis to file for GitHub Actions to read
        with open("llm_analysis.txt", "w") as f:
            f.write(analysis)

if __name__ == "__main__":
    main()
