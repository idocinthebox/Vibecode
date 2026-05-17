// Pre-test setup: mock vscode module for plain-node test runs
import * as fs from 'fs';
import * as path from 'path';

const testDir = __dirname;
const projectRoot = path.dirname(testDir);
const vscodeModuleDir = path.join(projectRoot, 'node_modules', 'vscode');
const vscodeMockPath = path.join(testDir, 'vscodeMock');

// Create a fake vscode package in node_modules if it doesn't exist
if (!fs.existsSync(vscodeModuleDir)) {
  fs.mkdirSync(vscodeModuleDir, { recursive: true });
  fs.writeFileSync(
    path.join(vscodeModuleDir, 'index.js'),
    `module.exports = require(${JSON.stringify(vscodeMockPath)});\n`
  );
  fs.writeFileSync(
    path.join(vscodeModuleDir, 'package.json'),
    JSON.stringify({ name: 'vscode', main: 'index.js', version: '99.0.0' })
  );
}
