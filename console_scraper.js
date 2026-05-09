// Paste this entire script into Chrome DevTools Console (F12 → Console tab)
// while on the NotJustAnalytics profile page

(function () {
    // Grab ALL text from the page body
    const allText = document.body.innerText;

    // Try to extract metrics by scanning all elements
    const allElements = document.querySelectorAll('*');
    const metrics = {};
    const labels = ['follower', 'following', 'post', 'e.r.', 'engagement', 'avg like', 'avg comment', 'average like', 'average comment', 'growth', 'authenticity', 'er'];

    // Method 1: Find labeled values (label near a number)
    allElements.forEach(el => {
        const text = el.innerText?.trim()?.toLowerCase();


        if (!text || text.length > 50) return; // skip long text blocks

        labels.forEach(label => {
            if (text === label || text === label + 's') {
                // Found a label - check siblings and parent for the value
                const parent = el.parentElement;
                if (parent) {
                    const siblings = Array.from(parent.children);
                    siblings.forEach(sib => {
                        const sibText = sib.innerText?.trim();
                        if (sib !== el && sibText && /[\d.,]+[KMB%]?/.test(sibText)) {
                            metrics[label] = sibText;
                        }
                    });
                    // Also check parent's text
                    const parentText = parent.innerText?.trim();
                    const numbers = parentText.match(/[\d.,]+[KMB%]?\s*/g);
                    if (numbers && !metrics[label]) {
                        metrics[label] = numbers[0].trim();
                    }
                }
            }
        });
    });

    // Method 2: Regex scan the full page text for common patterns
    const patterns = {
        followers_pattern: /(\d[\d.,]*[KMB]?)\s*(?:follower)/i,
        following_pattern: /(\d[\d.,]*[KMB]?)\s*(?:following)/i,
        posts_pattern: /(\d[\d.,]*[KMB]?)\s*(?:post)/i,
        er_pattern: /(\d[\d.,]*%?)\s*(?:e\.?r\.?|engagement\s*rate)/i,
        avg_likes_pattern: /(\d[\d.,]*[KMB]?)\s*(?:avg\.?\s*like|average\s*like)/i,
        avg_comments_pattern: /(\d[\d.,]*[KMB]?)\s*(?:avg\.?\s*comment|average\s*comment)/i,
        growth_pattern: /([+-]?\d[\d.,]*%?)\s*(?:growth|trend)/i,
    };

    const regexResults = {};
    for (const [key, pattern] of Object.entries(patterns)) {
        const match = allText.match(pattern);
        if (match) regexResults[key] = match[1];
    }

    // Also try reversed pattern: label THEN number
    const reversedPatterns = {
        followers_rev: /(?:follower)s?\s*[:\s]*(\d[\d.,]*[KMB]?)/i,
        following_rev: /(?:following)\s*[:\s]*(\d[\d.,]*[KMB]?)/i,
        posts_rev: /(?:post)s?\s*[:\s]*(\d[\d.,]*[KMB]?)/i,
        er_rev: /(?:e\.?r\.?|engagement\s*rate)\s*[:\s]*(\d[\d.,]*%?)/i,
    };

    for (const [key, pattern] of Object.entries(reversedPatterns)) {
        const match = allText.match(pattern);
        if (match) regexResults[key] = match[1];
    }

    // Build final output
    const result = {
        username: window.location.pathname.split('/').pop(),
        page_url: window.location.href,
        scraped_at: new Date().toISOString(),

        // From label scanning
        label_scan: metrics,

        // From regex scanning
        regex_scan: regexResults,

        // Raw text dump of the page (first 3000 chars for review)
        raw_page_text: allText.substring(0, 3000)
    };

    // Pretty print to console
    const jsonStr = JSON.stringify(result, null, 2);
    console.log("=== SCRAPED DATA ===");
    console.log(jsonStr);

    // Also copy to clipboard
    navigator.clipboard.writeText(jsonStr).then(() => {
        console.log("\n✅ JSON copied to clipboard! Paste it into info.JSON");
    }).catch(() => {
        console.log("\n⚠️ Couldn't copy to clipboard. Select the JSON above, right-click → Copy.");
    });

    return result;
})();
