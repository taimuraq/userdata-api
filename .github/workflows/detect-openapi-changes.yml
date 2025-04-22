name: Compare OpenAPI Spec Changes

on:
  pull_request:
    paths:
      - 'openapi-spec.json'
      - 'openapi-spec.yaml'

jobs:
  compare_openapi_specs:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          pip install deepdiff

      - name: Check for previous commit
        id: check_previous_commit
        run: |
          git log --oneline -n 2 || echo "No previous commit, using the current commit for comparison"

      - name: Fetch previous OpenAPI spec
        if: steps.check_previous_commit.outcome == 'success'
        run: |
          git checkout HEAD~1 openapi-spec.json || echo "No previous commit, skipping the checkout of old spec"

      - name: Compare OpenAPI Specs
        run: |
          python3 compare_openapi_specs.py
