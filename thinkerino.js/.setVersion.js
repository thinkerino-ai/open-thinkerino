const fs = require('fs');
const path = require('path');

const packageJsonPath = path.join(__dirname, 'package.json');
const newVersion = process.argv[2];

if (!newVersion) {
  console.error('Please provide a new version as a command-line argument.');
  process.exit(1);
}

fs.readFile(packageJsonPath, 'utf8', (readErr, data) => {
  if (readErr) {
    console.error(`Error reading package.json: ${readErr.message}`);
    process.exit(1);
  }

  let packageJson;
  try {
    packageJson = JSON.parse(data);
  } catch (parseErr) {
    console.error(`Error parsing package.json: ${parseErr.message}`);
    process.exit(1);
  }

  packageJson.version = newVersion;

  fs.writeFile(packageJsonPath, JSON.stringify(packageJson, null, 2), 'utf8', (writeErr) => {
    if (writeErr) {
      console.error(`Error writing package.json: ${writeErr.message}`);
      process.exit(1);
    }

    console.log(`Successfully updated the version to ${newVersion}`);
  });
});