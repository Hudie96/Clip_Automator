#!/usr/bin/env node
/**
 * Skill Evaluation Engine
 * Analyzes prompts and suggests relevant skills based on multiple signals
 * 
 * Usage: node skill-eval.js "<prompt>" "<rules-file>"
 */

const fs = require('fs');
const path = require('path');

// Confidence thresholds
const THRESHOLDS = {
    HIGH: 8,
    MEDIUM: 5,
    LOW: 3
};

// Point values for different match types
const POINTS = {
    keyword: 2,
    keywordPattern: 3,
    pathPattern: 4,
    directoryMatch: 5,
    intentPattern: 4
};

function loadRules(rulesFile) {
    try {
        const content = fs.readFileSync(rulesFile, 'utf8');
        return JSON.parse(content);
    } catch (e) {
        return null;
    }
}

function extractFilePaths(prompt) {
    // Match common file path patterns
    const patterns = [
        /(?:^|\s)((?:\.\/|\/)?(?:[\w-]+\/)*[\w-]+\.\w+)/g,  // ./path/file.ext or path/file.ext
        /`([^`]+\.\w+)`/g,  // `file.ext` in backticks
        /["']([^"']+\.\w+)["']/g  // "file.ext" or 'file.ext'
    ];
    
    const paths = [];
    for (const pattern of patterns) {
        let match;
        while ((match = pattern.exec(prompt)) !== null) {
            paths.push(match[1]);
        }
    }
    return [...new Set(paths)];
}

function evaluateSkill(prompt, skillName, skillConfig) {
    const promptLower = prompt.toLowerCase();
    const matches = [];
    let score = 0;
    
    const triggers = skillConfig.triggers || {};
    
    // Check keywords
    if (triggers.keywords) {
        for (const keyword of triggers.keywords) {
            if (promptLower.includes(keyword.toLowerCase())) {
                matches.push(`keyword "${keyword}"`);
                score += POINTS.keyword;
            }
        }
    }
    
    // Check keyword patterns (regex)
    if (triggers.keywordPatterns) {
        for (const pattern of triggers.keywordPatterns) {
            try {
                const regex = new RegExp(pattern, 'i');
                if (regex.test(prompt)) {
                    matches.push(`pattern /${pattern}/`);
                    score += POINTS.keywordPattern;
                }
            } catch (e) {
                // Invalid regex, skip
            }
        }
    }
    
    // Check file path patterns
    const extractedPaths = extractFilePaths(prompt);
    if (triggers.pathPatterns && extractedPaths.length > 0) {
        for (const pattern of triggers.pathPatterns) {
            const globToRegex = pattern
                .replace(/\*\*/g, '<<<GLOBSTAR>>>')
                .replace(/\*/g, '[^/]*')
                .replace(/<<<GLOBSTAR>>>/g, '.*')
                .replace(/\./g, '\\.');
            try {
                const regex = new RegExp(globToRegex);
                for (const filePath of extractedPaths) {
                    if (regex.test(filePath)) {
                        matches.push(`path "${filePath}"`);
                        score += POINTS.pathPattern;
                    }
                }
            } catch (e) {
                // Invalid pattern, skip
            }
        }
    }
    
    // Check intent patterns
    if (triggers.intentPatterns) {
        for (const pattern of triggers.intentPatterns) {
            try {
                const regex = new RegExp(pattern, 'i');
                if (regex.test(prompt)) {
                    matches.push(`intent /${pattern}/`);
                    score += POINTS.intentPattern;
                }
            } catch (e) {
                // Invalid regex, skip
            }
        }
    }
    
    // Check exclusion patterns
    if (skillConfig.excludePatterns) {
        for (const pattern of skillConfig.excludePatterns) {
            if (promptLower.includes(pattern.toLowerCase())) {
                // Exclusion matched, skip this skill
                return { score: 0, matches: [], excluded: true };
            }
        }
    }
    
    return { score, matches, excluded: false };
}

function main() {
    const prompt = process.argv[2];
    const rulesFile = process.argv[3];
    
    if (!prompt || !rulesFile) {
        process.exit(0);
    }
    
    const rules = loadRules(rulesFile);
    if (!rules) {
        process.exit(0);
    }
    
    const results = [];
    
    for (const [skillName, skillConfig] of Object.entries(rules)) {
        const evaluation = evaluateSkill(prompt, skillName, skillConfig);
        
        if (!evaluation.excluded && evaluation.score >= THRESHOLDS.LOW) {
            results.push({
                name: skillName,
                score: evaluation.score,
                matches: evaluation.matches,
                description: skillConfig.description || '',
                priority: skillConfig.priority || 5
            });
        }
    }
    
    // Sort by score (descending), then priority (descending)
    results.sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        return b.priority - a.priority;
    });
    
    if (results.length === 0) {
        process.exit(0);
    }
    
    // Build feedback message
    const extractedPaths = extractFilePaths(prompt);
    let feedback = '💡 **SKILL SUGGESTIONS**\n\n';
    
    if (extractedPaths.length > 0) {
        feedback += `📁 Detected files: ${extractedPaths.join(', ')}\n\n`;
    }
    
    feedback += 'Recommended skills:\n';
    
    for (let i = 0; i < Math.min(results.length, 3); i++) {
        const result = results[i];
        const confidence = result.score >= THRESHOLDS.HIGH ? 'HIGH' : 
                          result.score >= THRESHOLDS.MEDIUM ? 'MEDIUM' : 'LOW';
        
        feedback += `${i + 1}. **${result.name}** (${confidence})\n`;
        feedback += `   Matched: ${result.matches.slice(0, 3).join(', ')}\n`;
    }
    
    feedback += '\nUse: "Apply [skill-name] skill" to activate.';
    
    console.log(JSON.stringify({ feedback }));
}

main();
