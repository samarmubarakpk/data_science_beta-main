# Base directory
$baseDir = "frontend"

# Folder structure
$folders = @(
    "$baseDir/src",
    "$baseDir/src/ui",
    "$baseDir/src/ui/dialogs",
    "$baseDir/src/components",
    "$baseDir/src/utils",
    "$baseDir/src/resources/icons",
    "$baseDir/src/resources/styles",
    "$baseDir/src/resources/translations",
    "$baseDir/tests",
    "$baseDir/tests/test_components",
    "$baseDir/tests/test_ui"
)

# Files with placeholders
$files = @(
    "$baseDir/src/__init__.py",
    "$baseDir/src/main.py",
    "$baseDir/src/ui/__init__.py",
    "$baseDir/src/ui/main_window.py",
    "$baseDir/src/ui/canvas.py",
    "$baseDir/src/ui/component_palette.py",
    "$baseDir/src/ui/property_editor.py",
    "$baseDir/src/ui/dialogs/__init__.py",
    "$baseDir/src/ui/dialogs/settings.py",
    "$baseDir/src/ui/dialogs/about.py",
    "$baseDir/src/components/__init__.py",
    "$baseDir/src/components/base.py",
    "$baseDir/src/components/file_component.py",
    "$baseDir/src/components/cnn_component.py",
    "$baseDir/src/components/graph_component.py",
    "$baseDir/src/utils/__init__.py",
    "$baseDir/src/utils/config.py",
    "$baseDir/src/utils/style.py",
    "$baseDir/src/utils/logger.py",
    "$baseDir/tests/__init__.py"
)

# Create folders
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

# Create files
foreach ($file in $files) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

# Print completion message
Write-Host "Folder structure and files created successfully." -ForegroundColor Green
