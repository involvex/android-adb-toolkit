// apk_compare.js -- Compare two APKs (size, method count, manifest diffs)
// Usage: node apk_compare.js app1.apk app2.apk

const fs = require('fs');
const { execSync } = require('child_process');

async function compareAPKs(apk1, apk2) {
    console.log(`\n📦 APK Comparison`);
    console.log(`================`);
    
    // Size comparison
    const size1 = fs.statSync(apk1).size;
    const size2 = fs.statSync(apk2).size;
    const diff = size2 - size1;
    const pct = ((diff / size1) * 100).toFixed(1);
    
    console.log(`\nFile Size:`);
    console.log(`  ${apk1}: ${(size1 / 1024 / 1024).toFixed(2)} MB`);
    console.log(`  ${apk2}: ${(size2 / 1024 / 1024).toFixed(2)} MB`);
    console.log(`  Difference: ${diff > 0 ? '+' : ''}${(diff / 1024 / 1024).toFixed(2)} MB (${pct}%)`);
    
    // Aapt info
    try {
        const info1 = execSync(`aapt dump badging ${apk1}`).toString();
        const info2 = execSync(`aapt dump badging ${apk2}`).toString();
        
        const ver1 = info1.match(/versionName='([^']+)'/)?.[1] || 'unknown';
        const ver2 = info2.match(/versionName='([^']+)'/)?.[1] || 'unknown';
        
        console.log(`\nVersions:`);
        console.log(`  ${apk1}: ${ver1}`);
        console.log(`  ${apk2}: ${ver2}`);
        
        // Permissions diff
        const perms1 = new Set(info1.match(/uses-permission: name='([^']+)'/g) || []);
        const perms2 = new Set(info2.match(/uses-permission: name='([^']+)'/g) || []);
        
        const added = [...perms2].filter(p => !perms1.has(p));
        const removed = [...perms1].filter(p => !perms2.has(p));
        
        if (added.length > 0 || removed.length > 0) {
            console.log(`\nPermission Changes:`);
            if (added.length) console.log(`  Added (${added.length}): ${added.slice(0, 3).join(', ')}`);
            if (removed.length) console.log(`  Removed (${removed.length}): ${removed.slice(0, 3).join(', ')}`);
        }
    } catch(e) {
        console.log("  (aapt not available)");
    }
}

const [apk1, apk2] = process.argv.slice(2);
if (!apk1 || !apk2) {
    console.log('Usage: node apk_compare.js <apk1> <apk2>');
    process.exit(1);
}
compareAPKs(apk1, apk2);
