import yaml
import json
import sys
import subprocess
from openai import OpenAI
import os


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_oasdiff(old_spec_path, new_spec_path):
    result = subprocess.run([
        "oasdiff", "diff",
        old_spec_path,
        new_spec_path,
        "--format", "json"
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running oasdiff:", result.stderr)
        sys.exit(1)
    return json.loads(result.stdout)

def extract_changed_operations(oasdiff_output):
    changes = []
    paths = oasdiff_output.get("paths", {})

    # Handle modified paths
    modified = paths.get("modified", [])
    if isinstance(modified, dict):
        for path, methods in modified.items():
            for method in methods.get("operations", {}).get("modified", {}):
                changes.append({"method": method.upper(), "path": path})
    elif isinstance(modified, list):
        for entry in modified:
            path = entry.get("path")
            for method in entry.get("operations", {}).get("modified", {}):
                changes.append({"method": method.upper(), "path": path})

    # Handle added paths
    added = paths.get("added", {})
    if isinstance(added, dict):
        for path, methods in added.items():
            for method in methods.get("operations", {}):
                changes.append({"method": method.upper(), "path": path})
    elif isinstance(added, list):  # <-- handle list case
        for path in added:
            changes.append({"method": "ANY", "path": path})  # we don't know method here

    # Handle deleted paths
    deleted = paths.get("deleted", {})
    if isinstance(deleted, dict):
        for path, methods in deleted.items():
            for method in methods.get("operations", {}):
                changes.append({"method": method.upper(), "path": path})
    elif isinstance(deleted, list):  # <-- handle list case
        for path in deleted:
            changes.append({"method": "ANY", "path": path})  # we don't know method here either

    return changes


def analyze_impact(changed_paths, dependencies):
    impacted = []
    for dep in dependencies:
        ext_path = dep['externalCall']['path']
        ext_method = dep['externalCall']['method'].upper()
        for change in changed_paths:
            if change['path'] == ext_path and (change['method'] == "ANY" or change['method'] == ext_method):
                impacted.append(dep)
                break
    return impacted

def build_llm_prompt(changed_paths, impacted_deps):
    return {
        "task": "Analyze the impact of API changes on dependent services.",
        "changes": changed_paths,
        "dependencies": impacted_deps,
        "instructions": "For each changed path, list impacted APIs from dependencies and explain why."
    }

def call_openai(prompt):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert in OpenAPI change analysis."},
            {"role": "user", "content": json.dumps(prompt)}
        ]
    )
    return response.choices[0].message.content

def main():
    old_spec_path = sys.argv[1]
    new_spec_path = sys.argv[2]
    dependencies = load_json(sys.argv[3])

    print("🧪 Running oasdiff...")
    oasdiff_output = run_oasdiff(old_spec_path, new_spec_path)
    changed_paths = extract_changed_operations(oasdiff_output)

    print("🔍 Changed OpenAPI operations:")
    for p in changed_paths:
        print(f" - {p['method']} {p['path']}")

    impacted = analyze_impact(changed_paths, dependencies)

    if not impacted:
        print("\n⚠️ No impacted services or endpoints.")
        return

    prompt = build_llm_prompt(changed_paths, impacted)

    print (prompt)
    print("\n🤖 Sending prompt to OpenAI...")
    analysis = call_openai(prompt)
    print("\n📋 LLM Impact Analysis Result:")
    print(analysis)

if __name__ == "__main__":
    main()
