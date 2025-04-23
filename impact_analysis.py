
import yaml
import json
import sys
from deepdiff import DeepDiff
import subprocess  # Add this import
import os          # Add this import
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_oasdiff(old_spec_path, new_spec_path):
    result = subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/specs",
        "tufin/oasdiff:latest",
        "diff",
        f"/specs/{old_spec_path}",
        f"/specs/{new_spec_path}",
        "--format", "json"  # Changed from --output-format to --format
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("Error running oasdiff:", result.stderr)
        sys.exit(1)
    return json.loads(result.stdout)

# parse and extraxt info from oasdiff response
def extract_major_changes(oasdiff_output):
    summary = {
        "added_properties": set(),
        "removed_properties": set(),
        "modified_endpoints": set(),
        "breaking_changes": []
    }

    # Extract path changes
    if "paths" in oasdiff_output:
        paths = oasdiff_output["paths"]

        # Check modified paths
        if "modified" in paths:
            for path, details in paths["modified"].items():
                summary["modified_endpoints"].add(path)

                # Check operations
                if "operations" in details and "modified" in details["operations"]:
                    for method, op_changes in details["operations"]["modified"].items():
                        # Check request changes
                        if "requestBody" in op_changes:
                            req_body = op_changes["requestBody"]
                            if "content" in req_body:
                                for media_type, content in req_body["content"].items():
                                    if "mediaTypeModified" in content:
                                        for _, schema_changes in content["mediaTypeModified"].items():
                                            if "schema" in schema_changes and "properties" in schema_changes["schema"]:
                                                props = schema_changes["schema"]["properties"]
                                                if "added" in props:
                                                    summary["added_properties"].update(props["added"])
                                                if "removed" in props:
                                                    summary["removed_properties"].update(props["removed"])

                        # Check response changes
                        if "responses" in op_changes and "modified" in op_changes["responses"]:
                            for status, resp_changes in op_changes["responses"]["modified"].items():
                                if "content" in resp_changes:
                                    for media_type, content in resp_changes["content"].items():
                                        if "mediaTypeModified" in content:
                                            for _, schema_changes in content["mediaTypeModified"].items():
                                                if "schema" in schema_changes and "properties" in schema_changes["schema"]:
                                                    props = schema_changes["schema"]["properties"]
                                                    if "added" in props:
                                                        summary["added_properties"].update(props["added"])
                                                    if "removed" in props:
                                                        summary["removed_properties"].update(props["removed"])

    # Check schema changes
    if "components" in oasdiff_output and "schemas" in oasdiff_output["components"]:
        schemas = oasdiff_output["components"]["schemas"]
        if "modified" in schemas:
            for schema, changes in schemas["modified"].items():
                if "properties" in changes:
                    props = changes["properties"]
                    if "added" in props:
                        summary["added_properties"].update(props["added"])
                    if "removed" in props:
                        summary["removed_properties"].update(props["removed"])

    # Convert sets to lists for JSON serialization
    summary["added_properties"] = list(summary["added_properties"])
    summary["removed_properties"] = list(summary["removed_properties"])
    summary["modified_endpoints"] = list(summary["modified_endpoints"])

    return summary


def analyze_api_changes(diff_output):
    changes = {
        "path_changes": [],
        "schema_changes": []
    }

    # Extract path changes
    if "paths" in diff_output:
        paths = diff_output["paths"]

        # Handle added paths
        if "added" in paths:
            for path in paths["added"]:
                changes["path_changes"].append({
                    "change_type": "added",
                    "path": path,
                    "http_methods": "ALL",  # We don't have detailed method info for added paths
                    "details": "New endpoint added"
                })

        # Handle deleted paths
        if "deleted" in paths:
            for path in paths["deleted"]:
                changes["path_changes"].append({
                    "change_type": "deleted",
                    "path": path,
                    "http_methods": "ALL",  # We don't have detailed method info for deleted paths
                    "details": "Endpoint removed"
                })

        # Handle modified paths
        if "modified" in paths:
            for path, details in paths["modified"].items():
                if "operations" in details and "modified" in details["operations"]:
                    for method, op_changes in details["operations"]["modified"].items():
                        # Extract detailed changes for this method
                        method_changes = []

                        # Check request body changes
                        if "requestBody" in op_changes:
                            req_body = op_changes["requestBody"]
                            if "content" in req_body:
                                for media_type, content in req_body["content"].items():
                                    if "mediaTypeModified" in content:
                                        for content_type, schema_changes in content["mediaTypeModified"].items():
                                            if "schema" in schema_changes:
                                                schema = schema_changes["schema"]
                                                if "properties" in schema:
                                                    props = schema["properties"]
                                                    if "added" in props:
                                                        method_changes.append(
                                                            f"Added request properties: {', '.join(props['added'])}")
                                                    if "removed" in props:
                                                        method_changes.append(
                                                            f"Removed request properties: {', '.join(props['removed'])}")

                        # Check response changes
                        if "responses" in op_changes and "modified" in op_changes["responses"]:
                            for status, resp_changes in op_changes["responses"]["modified"].items():
                                if "content" in resp_changes:
                                    for media_type, content in resp_changes["content"].items():
                                        if "mediaTypeModified" in content:
                                            for content_type, schema_changes in content["mediaTypeModified"].items():
                                                if "schema" in schema_changes:
                                                    schema = schema_changes["schema"]
                                                    if "properties" in schema:
                                                        props = schema["properties"]
                                                        if "added" in props:
                                                            method_changes.append(
                                                                f"Added response properties in {status}: {', '.join(props['added'])}")
                                                        if "removed" in props:
                                                            method_changes.append(
                                                                f"Removed response properties in {status}: {', '.join(props['removed'])}")

                        changes["path_changes"].append({
                            "change_type": "modified",
                            "path": path,
                            "http_methods": method,
                            "details": method_changes if method_changes else "Operation modified without property changes"
                        })

    # Extract schema changes
    if "components" in diff_output and "schemas" in diff_output["components"]:
        schemas = diff_output["components"]["schemas"]
        if "modified" in schemas:
            for schema_name, schema_changes in schemas["modified"].items():
                schema_detail = {
                    "schema_name": schema_name,
                    "changes": []
                }

                if "properties" in schema_changes:
                    props = schema_changes["properties"]
                    if "added" in props:
                        schema_detail["changes"].append(f"Added properties: {props['added']}")
                    if "removed" in props:
                        schema_detail["changes"].append(f"Removed properties: {props['removed']}")

                changes["schema_changes"].append(schema_detail)

    return changes


def analyze_oasdiff_changes(diff_output):
    changes = {
        "endpoint_changes": [],
        "property_changes": []
    }

    # Extract path changes
    if "paths" in diff_output:
        paths = diff_output.get("paths", {})

        # Handle path additions and deletions
        for added_path in paths.get("added", []):
            changes["endpoint_changes"].append({
                "type": "added",
                "path": added_path
            })

        for deleted_path in paths.get("deleted", []):
            changes["endpoint_changes"].append({
                "type": "deleted",
                "path": deleted_path
            })

        # Handle modified paths
        modified_paths = paths.get("modified", {})
        for path, path_changes in modified_paths.items():
            operations = path_changes.get("operations", {}).get("modified", {})

            for method, op_changes in operations.items():
                endpoint_change = {
                    "type": "modified",
                    "path": path,
                    "method": method,
                    "request_changes": [],
                    "response_changes": []
                }

                # Check request body changes
                if "requestBody" in op_changes:
                    req_content = op_changes.get("requestBody", {}).get("content", {})
                    for media_type, media_changes in req_content.items():
                        if "mediaTypeModified" in media_changes:
                            for content_type, schema_info in media_changes.get("mediaTypeModified", {}).items():
                                schema = schema_info.get("schema", {})
                                properties = schema.get("properties", {})

                                if "added" in properties:
                                    endpoint_change["request_changes"].append({
                                        "type": "properties_added",
                                        "properties": properties.get("added", [])
                                    })

                                if "removed" in properties:
                                    endpoint_change["request_changes"].append({
                                        "type": "properties_removed",
                                        "properties": properties.get("removed", [])
                                    })

                # Check response changes
                if "responses" in op_changes:
                    responses = op_changes.get("responses", {}).get("modified", {})
                    for status, resp_changes in responses.items():
                        if "content" in resp_changes:
                            for media_type, media_changes in resp_changes.get("content", {}).items():
                                if "mediaTypeModified" in media_changes:
                                    for content_type, schema_info in media_changes.get("mediaTypeModified", {}).items():
                                        schema = schema_info.get("schema", {})
                                        properties = schema.get("properties", {})

                                        if "added" in properties:
                                            endpoint_change["response_changes"].append({
                                                "type": "properties_added",
                                                "status": status,
                                                "properties": properties.get("added", [])
                                            })

                                        if "removed" in properties:
                                            endpoint_change["response_changes"].append({
                                                "type": "properties_removed",
                                                "status": status,
                                                "properties": properties.get("removed", [])
                                            })

                changes["endpoint_changes"].append(endpoint_change)

    # Extract schema changes
    if "components" in diff_output and "schemas" in diff_output.get("components", {}):
        schemas = diff_output.get("components", {}).get("schemas", {})
        modified_schemas = schemas.get("modified", {})

        for schema_name, schema_changes in modified_schemas.items():
            if "properties" in schema_changes:
                properties = schema_changes.get("properties", {})

                if "added" in properties:
                    changes["property_changes"].append({
                        "type": "schema_properties_added",
                        "schema": schema_name,
                        "properties": properties.get("added", [])
                    })

                if "removed" in properties:
                    changes["property_changes"].append({
                        "type": "schema_properties_removed",
                        "schema": schema_name,
                        "properties": properties.get("removed", [])
                    })

    return changes


def analyze_impact(api_changes, dependencies):
    impacted_services = []

    # Create lookup maps for faster matching
    endpoint_changes_by_path = {}
    for change in api_changes["endpoint_changes"]:
        path = change["path"]
        if path not in endpoint_changes_by_path:
            endpoint_changes_by_path[path] = []
        endpoint_changes_by_path[path].append(change)

    # Map of deleted paths to their potential replacements
    path_replacements = {}
    deleted_paths = [c["path"] for c in api_changes["endpoint_changes"] if c["type"] == "deleted"]
    added_paths = [c["path"] for c in api_changes["endpoint_changes"] if c["type"] == "added"]

    for deleted in deleted_paths:
        for added in added_paths:
            # Check if this looks like a versioned replacement (e.g., /users/{id} → /users/v1/{id})
            if normalize_path(deleted) == normalize_path(added):
                path_replacements[deleted] = added

    # Analyze each dependency
    for dependency in dependencies:
        service_name = dependency.get("serviceName")
        external_call = dependency.get("externalCall", {})
        dependent_path = external_call.get("path")
        dependent_method = external_call.get("method", "").upper()

        impact_details = []

        # Check if the dependent path was deleted
        if dependent_path in deleted_paths:
            replacement = path_replacements.get(dependent_path)
            if replacement:
                impact_details.append({
                    "impact_type": "breaking",
                    "change_type": "path_versioned",
                    "description": f"Endpoint moved from {dependent_path} to {replacement}",
                    "before": dependent_path,
                    "after": replacement,
                    "severity": "high"
                })
            else:
                impact_details.append({
                    "impact_type": "breaking",
                    "change_type": "path_removed",
                    "description": f"Endpoint {dependent_path} was completely removed",
                    "before": dependent_path,
                    "after": "None",
                    "severity": "critical"
                })

        # Check if the dependent path was modified
        if dependent_path in endpoint_changes_by_path:
            for change in endpoint_changes_by_path[dependent_path]:
                # Skip if this is not the method we're interested in
                if change.get("method") and change.get("method").upper() != dependent_method:
                    continue

                # Check request changes
                for req_change in change.get("request_changes", []):
                    if req_change["type"] == "properties_added":
                        impact_details.append({
                            "impact_type": "non-breaking",
                            "change_type": "request_properties_added",
                            "description": f"Request properties added: {', '.join(req_change['properties'])}",
                            "properties": req_change['properties'],
                            "severity": "low"
                        })
                    elif req_change["type"] == "properties_removed":
                        impact_details.append({
                            "impact_type": "breaking",
                            "change_type": "request_properties_removed",
                            "description": f"Request properties removed: {', '.join(req_change['properties'])}",
                            "properties": req_change['properties'],
                            "severity": "high"
                        })

                # Check response changes
                for resp_change in change.get("response_changes", []):
                    if resp_change["type"] == "properties_added":
                        impact_details.append({
                            "impact_type": "non-breaking",
                            "change_type": "response_properties_added",
                            "description": f"Response properties added in status {resp_change['status']}: {', '.join(resp_change['properties'])}",
                            "properties": resp_change['properties'],
                            "status": resp_change['status'],
                            "severity": "low"
                        })
                    elif resp_change["type"] == "properties_removed":
                        impact_details.append({
                            "impact_type": "breaking",
                            "change_type": "response_properties_removed",
                            "description": f"Response properties removed in status {resp_change['status']}: {', '.join(resp_change['properties'])}",
                            "properties": resp_change['properties'],
                            "status": resp_change['status'],
                            "severity": "high"
                        })

        # Look for schema changes that might affect this dependency
        # This is more of a heuristic since we don't know exactly which schemas this endpoint uses
        schema_impacts = []
        for schema_change in api_changes.get("property_changes", []):
            if schema_change["type"] == "schema_properties_added":
                schema_impacts.append({
                    "impact_type": "non-breaking",
                    "change_type": "schema_properties_added",
                    "description": f"Properties added to {schema_change['schema']} schema: {', '.join(schema_change['properties'])}",
                    "schema": schema_change['schema'],
                    "properties": schema_change['properties'],
                    "severity": "low"
                })
            elif schema_change["type"] == "schema_properties_removed":
                schema_impacts.append({
                    "impact_type": "breaking",
                    "change_type": "schema_properties_removed",
                    "description": f"Properties removed from {schema_change['schema']} schema: {', '.join(schema_change['properties'])}",
                    "schema": schema_change['schema'],
                    "properties": schema_change['properties'],
                    "severity": "high"
                })

        # Add schema impacts only if we found other impacts
        # (to avoid noise from unrelated schema changes)
        if impact_details and schema_impacts:
            impact_details.extend(schema_impacts)

        # If we found any impacts, add this service to the results
        if impact_details:
            impacted_services.append({
                "service": service_name,
                "affected_endpoint": {
                    "path": dependent_path,
                    "method": dependent_method
                },
                "originatingEndpoints": dependency.get("originatingEndpoints", []),
                "impact_details": impact_details
            })

    return impacted_services


def normalize_path(path):
    """Normalize API paths to handle version differences and parameter names"""
    import re

    # Remove version segments (e.g., /v1/, /v2/)
    normalized = re.sub(r'/v\d+/', '/', path)

    # Replace all parameter placeholders with a generic {param}
    normalized = re.sub(r'\{[^}]+\}', '{param}', normalized)

    return normalized

def extract_changed_paths(diff):
    changed = set()
    for category in ['values_changed', 'dictionary_item_added', 'dictionary_item_removed']:
        for path in diff.get(category, {}):
            if path.startswith("root['paths']"):
                parts = path.split("'")
                if len(parts) >= 4:
                    changed.add(parts[3])
    return changed

# def analyze_impact(changed_paths, dependencies):
#     impacted = []
#     for dep in dependencies:
#         external_path = dep['externalCall']['path']
#         for changed in changed_paths:
#             if external_path in changed:
#                 impacted.append(dep)
#                 break
#     return impacted

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


def build_llm_prompt(oasdiff_output, dependencies):
    prompt = {
        "task": "API Impact Analysis",
        "api_changes": oasdiff_output,
        "dependencies": dependencies,
        "instructions": """
        Analyze the impact of the API changes on the dependent services. Assume that all services are written in Java.

        1. Identify which API endpoints have changed (added, deleted, modified)
        2. Determine if any dependent services use these endpoints
        3. Assess the severity of the impact (breaking vs. non-breaking changes)
        4. Provide specific recommendations for updating the dependent services

        For each impacted service:
        - Highlight the specific internal code paths (using the internalTrace information) that will need updates
        - For each affected code path, describe exactly what needs to be changed
        - Prioritize changes based on severity (critical, high, medium, low)

        Format your response with clear sections:
        - Summary of API Changes
        - Impacted Services and Code Paths
        - Required Updates (with code examples where appropriate)
        - Recommended Testing Approach

        Focus particularly on breaking changes such as:
        - Removed endpoints
        - Versioned endpoints (e.g., /resource → /v1/resource)
        - Removed properties or parameters
        - Changed data types
        """
    }

    return prompt


def call_openai_with_mcp(oasdiff_output, dependencies):

    # Structure the request using supported MCP format
    mcp_request = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert API architect specializing in API versioning, compatibility, and change management."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze the impact of these API changes on the dependent services."
                    },
                    {
                        "type": "text",
                        "text": f"API Diff Output: {json.dumps(oasdiff_output, indent=2)}"
                    },
                    {
                        "type": "text",
                        "text": f"Service Dependencies: {json.dumps(dependencies, indent=2)}"
                    },
                    {
                        "type": "text",
                        "text": """
                        In your analysis:
                        1. Identify all breaking and non-breaking changes.
                        2. For each impacted service, highlight the affected internal code paths using internalTrace information
                        3. Provide specific recommendations for updating each affected component
                        4. Prioritize changes based on severity

                        Format your response with clear sections:
                        - Summary of API Changes. First show them in a list, then explain them
                        - Impacted Services and Code Paths. First show them in a list, then explain them
                        - Required Updates (with code examples)
                        - Recommended Testing Strategy
                        """
                    }
                ]
            }
        ]
    }

    try:
        response = client.chat.completions.create(**mcp_request)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API with MCP: {e}")
        return None


def call_openai(prompt):

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are an expert API architect specializing in API versioning, compatibility, and change management."},
                {"role": "user", "content": json.dumps(prompt, indent=2)}
            ],
            temperature=0.1  # Lower temperature for more precise analysis
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

# def call_openai(prompt):
#     response = client.chat.completions.create(
#         model="gpt-4",
#         messages=prompt,
#         temperature=0.3
#     )
#     return response.choices[0].message.content

def main():
    old_spec = load_yaml(sys.argv[1])
    new_spec = load_yaml(sys.argv[2])
    dependencies = load_json(sys.argv[3])

    # Add this before your main run_oasdiff function call
    # to debug and see available options
    help_result = subprocess.run([
        "docker", "run", "--rm", "tufin/oasdiff:latest", "diff", "--help"
    ], capture_output=True, text=True)
    print("Available options:")
    print(help_result.stdout)

    oasdiff_result = run_oasdiff(sys.argv[1], sys.argv[2])

    print(oasdiff_result)

    # After running oasdiff and loading dependencies
    # prompt = build_llm_prompt(oasdiff_result, dependencies)
    # print(prompt)
    # analysis = call_openai(prompt)

    # After running oasdiff and loading dependencies
    analysis = call_openai_with_mcp(oasdiff_result, dependencies)

    print("\n📋 MCP-Enhanced LLM Analysis:")
    print(analysis)

    print("\n📋 LLM Impact Analysis:")
    print(analysis)

    # Analyze API changes in detail

    # ✍️ Write analysis to file for GitHub Actions to read
    with open("llm_analysis.txt", "w") as f:
        f.write(analysis)

if __name__ == "__main__":
    main()
