const fs = require('fs');
const path = require('path');

function removeComments(filePath) {
    try {
        let content = fs.readFileSync(filePath, 'utf8');
        // Remove multi-line comments
        content = content.replace(/\/\*[\s\S]*?\*\//g, '');
        // Remove single-line comments (careful not to match http://)
        content = content.replace(/(?<!:)\/\/.*/g, '');
        
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`Stripped: ${filePath}`);
    } catch (e) {
        console.error(`Skipped ${filePath}: ${e.message}`);
    }
}

function processDirectory(dir) {
    if (!fs.existsSync(dir)) return;
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            if (file !== 'node_modules' && file !== '.next' && file !== 'dist' && !file.startsWith('.')) {
                processDirectory(fullPath);
            }
        } else if (file.match(/\.(js|jsx|ts|tsx)$/)) {
            removeComments(fullPath);
        }
    }
}

processDirectory('./frontend');
