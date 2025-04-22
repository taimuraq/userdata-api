import json
import sys

def analyze_impact(dependencies_file):
    with open(dependencies_file, 'r') as file:
        dependencies = json.load(file)
    
    impacted_services = []
    for external_call in dependencies['externalCalls']:
        for originating_endpoint in external_call['originatingEndpoints']:
            if 'userdata-api' in originating_endpoint['api']:  # Check if this is the current service
                impacted_services.append(external_call['service'])
    
    if impacted_services:
        print("This change might impact the following services:", impacted_services)
    else:
        print("No impact detected.")

if __name__ == "__main__":
    dependencies_file = sys.argv[1]
    analyze_impact(dependencies_file)
