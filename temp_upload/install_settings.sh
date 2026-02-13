#!/bin/bash
# Script to install SettingResource files with proper permissions

echo "Installing SettingResource to Central Panel..."

# Create directory structure
sudo mkdir -p ~/my-project/app/Filament/Central/Resources/SettingResource/Pages

# Copy files
sudo cp ~/temp_upload/SettingResource.php ~/my-project/app/Filament/Central/Resources/
sudo cp ~/temp_upload/ManageSettings.php ~/my-project/app/Filament/Central/Resources/SettingResource/Pages/

# Set ownership
sudo chown -R almalinux:almalinux ~/my-project/app/Filament/Central/Resources/SettingResource

# Verify
echo "Files installed:"
ls -la ~/my-project/app/Filament/Central/Resources/SettingResource.php
ls -la ~/my-project/app/Filament/Central/Resources/SettingResource/Pages/ManageSettings.php

echo "Done!"
