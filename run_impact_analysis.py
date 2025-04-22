import json
import sys

def analyze_impact(dependencies_file):
    # Read the dependencies JSON file
    with open(dependencies_file, 'r') as file:
        dependencies = json.load(file)
    
    impacted_services = []

    # Iterate through each dependency record
    for record in dependencies:
        external_call = record['externalCall']
        originating_endpoints = record['originatingEndpoints']

        # Check if the external call is to userdata-api (assuming that's the service to track for changes)
        if external_call['service'] == 'userdataapi':
            for originating_endpoint in originating_endpoints:
                # Check if any originating endpoint is using the userdata-api
                if 'userdataapi' in external_call['service']:
                    impacted_services.append(external_call['service'])
    
    # Output the impacted services based on changes
    if impacted_services:
        print("This change might impact the following services:", impacted_services)
    else:
        print("No impact detected.")

if __name__ == "__main__":
    # Pass the dependencies file as a command-line argument
    dependencies_file = sys.argv[1]
    analyze_impact(dependencies_file)
