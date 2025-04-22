import json
import sys

def analyze_impact(dependencies_file):
    with open(dependencies_file, 'r') as file:
        dependencies = json.load(file)
    
    impacted_services = []
    
    # Iterate over external calls to find any dependencies on 'userdata-api'
    for external_call in dependencies['externalCall']:
        if external_call['service'] == 'userdataapi':  # If 'userdata-api' is the external service
            for originating_endpoint in external_call['originatingEndpoints']:
                # If 'userdata-api' is being used in originating endpoints, add to impacted services
                impacted_services.append(originating_endpoint['api'])
    
    if impacted_services:
        print("This change might impact the following services:", impacted_services)
    else:
        print("No impact detected.")

if __name__ == "__main__":
    dependencies_file = sys.argv[1]
    analyze_impact(dependencies_file)

