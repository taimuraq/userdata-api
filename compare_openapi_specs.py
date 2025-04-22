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

      - name: Check if previous commit exists
        id: check_previous_commit
        run: |
          git rev-parse --verify HEAD~1 || echo "No previous commit, skipping checkout"

      - name: Download old OpenAPI spec from previous commit
        if: steps.check_previous_commit.outcome == 'success'
        run: |
          git checkout HEAD~1 openapi-spec.json
          mv openapi-spec.json openapi-spec-old.json

      - name: Compare OpenAPI Specs
        run: |
          python3 compare_openapi_specs.py
