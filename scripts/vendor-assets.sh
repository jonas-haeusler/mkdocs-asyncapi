#!/bin/bash
set -eou pipefail

# Maintainer script: refreshes the AsyncAPI web component JS + CSS vendored
# into mkdocs_asyncapi/assets/. Run after bumping the version in package.json.

cd "$(dirname "$0")/.."

npm install --no-audit --no-fund

cp node_modules/@asyncapi/web-component/lib/asyncapi-web-component.js mkdocs_asyncapi/assets/
cp node_modules/@asyncapi/react-component/styles/default.min.css mkdocs_asyncapi/assets/

python3 scripts/rem_to_px.py mkdocs_asyncapi/assets/default.min.css

echo "Vendored assets updated in mkdocs_asyncapi/assets/"
