// Paste this into Chrome DevTools Console (F12 → Console tab)
// while on the NotJustAnalytics profile analysis page
// First time: type "allow pasting" and press Enter

(function () {
    // --- Helper: parse numbers like "1,124,624" or "17M" or "1.128.112" ---
    function parseNum(text) {
        if (!text) return 0;
        text = text.trim();

        // Handle K/M/B suffixes (e.g., "17M", "2.5K")
        const suffixMatch = text.match(/^([\d.,]+)\s*([KMB])$/i);
        if (suffixMatch) {
            const num = parseFloat(suffixMatch[1].replace(/,/g, ''));
            const mult = { K: 1000, M: 1000000, B: 1000000000 }[suffixMatch[2].toUpperCase()];
            return num * mult;
        }

        // Detect European format: "1.128.112" (dots as thousands, no comma)
        // vs standard: "1,124,624" (commas as thousands)
        if (/^\d{1,3}(\.\d{3}){2,}$/.test(text)) {
            // European format — dots are thousands separators
            return parseInt(text.replace(/\./g, ''), 10);
        }

        // Standard format — commas are thousands separators
        return parseFloat(text.replace(/,/g, '')) || 0;
    }

    // --- Helper: find value by DOM label (most reliable) ---
    function findByLabel(labelText) {
        const allEls = document.querySelectorAll('*');
        for (const el of allEls) {
            const t = el.innerText?.trim()?.toLowerCase();
            if (t === labelText || t === labelText + 's') {
                const parent = el.parentElement;
                if (!parent) continue;
                // Check sibling elements for a number
                for (const sib of parent.children) {
                    if (sib === el) continue;
                    const sibText = sib.innerText?.trim();
                    if (sibText && /^[\d.,]+[KMB]?$/.test(sibText)) {
                        return sibText;
                    }
                }
            }
        }
        return null;
    }

    // --- Helper: find value from raw text (NUMBER before LABEL) ---
    function findBeforeLabel(label) {
        const allText = document.body.innerText;
        // Match: number on one line, label on next line
        const regex = new RegExp('([\\d.,]+[KMB]?)\\s*\\n\\s*' + label, 'i');
        const match = allText.match(regex);
        return match ? match[1] : null;
    }

    // --- Helper: extract daily growth from "Average followers per day" ---
    function findDailyGrowth() {
        const allText = document.body.innerText;
        const match = allText.match(/([-+]?[\d.,]+)\s*\n\s*Average followers per day/i);
        return match ? parseNum(match[1]) : 0;
    }

    // --- Extract each metric using the best method ---
    // Followers: use regex (label_scan returns European format)
    const followersRaw = findBeforeLabel('Followers');
    const followers = parseNum(followersRaw);

    // Following & Posts: use DOM label scan (regex grabs weekly changes)
    const followingRaw = findByLabel('following');
    const following = parseNum(followingRaw);

    const postsRaw = findByLabel('post');
    const postsCount = parseNum(postsRaw);

    // Avg Likes & Comments: both methods agree, use either
    const avgLikesRaw = findByLabel('avg like') || findBeforeLabel('Avg likes');
    const avgLikes = parseNum(avgLikesRaw);

    const avgCommentsRaw = findByLabel('avg comment') || findBeforeLabel('Avg comments');
    const avgComments = parseNum(avgCommentsRaw);

    // Engagement Rate: calculated (site locks it behind login)
    const engagementRate = followers > 0
        ? Math.round(((avgLikes + avgComments) / followers) * 10000) / 100
        : 0;

    // Growth Rate: convert daily followers change → monthly percentage
    const dailyGrowth = findDailyGrowth();
    const growthRate = followers > 0
        ? Math.round((dailyGrowth * 30 / followers) * 1000) / 10
        : 0;

    // Username: from URL
    const username = window.location.pathname.split('/').pop();

    // --- Build final output matching client.py format ---
    const result = {
        username: username,
        followers: followers,
        following: following,
        posts_count: postsCount,
        engagement_rate: engagementRate,
        avg_likes: avgLikes,
        avg_comments: avgComments,
        growth_rate: growthRate,
        authenticity_score: 0
    };

    // Pretty print
    const jsonStr = JSON.stringify(result, null, 4);
    console.log("=== CLEANED DATA FOR info.JSON ===");
    console.log(jsonStr);

    // Copy to clipboard
    navigator.clipboard.writeText(jsonStr).then(() => {
        console.log("\n✅ Copied to clipboard! Paste into info.JSON");
    }).catch(() => {
        console.log("\n⚠️ Couldn't auto-copy. Select the JSON above → right-click → Copy");
    });

    return result;
})();