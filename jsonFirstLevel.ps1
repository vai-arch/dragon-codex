# Path to your JSON file
$jsonPath = "data\metadata\wiki\category_to_files.json"

# Load and convert JSON
$json = Get-Content $jsonPath -Raw | ConvertFrom-Json

# Print first-level entries (keys)
$json.PSObject.Properties.Name
