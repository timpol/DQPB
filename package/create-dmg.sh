#!/usr/bin/env bash

# Get the root folder.
ROOT="${PWD}"

# Path to the built application.
APP="${ROOT}"/dist/DQPB.app

# Create the artifacts folder if if doesn't exits
ARTIFACTS="${ROOT}"/artifacts
[ ! -d "$ARTIFACTS" ] && mkdir -p "$ARTIFACTS"

echo "Removing previous images."
if [[ -e "${DMG}" ]]; then rm -rf "${DMG}"; fi

# Delete any old versions before running this script.

# Path to create_dmg executable
# CREATE_DMG=../dev/create-dmg-master/create-dmg
# Assume create-dmg is installed
CREATE_DMG="create-dmg"

# Create the DMG
# version appended to .dmg filename later
$CREATE_DMG \
  --volname "DQPB Installer" \
  --background "dmg-background.png" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "DQPB.app" 200 190 \
  --hide-extension "DQPB.app" \
  --app-drop-link 600 185 \
  "${ARTIFACTS}/DQPB.dmg" \
  "${APP}"