# extractor.py
# The actual scraping/extraction logic — JavaScript that runs inside the browser
# This is the "bs4 equivalent" — it parses the page content and extracts metrics
#
# Called by scraper.py via: driver.execute_script(EXTRACT_JS)

# ---------------------------------------------------------------------------
# JavaScript extraction code (same logic as console_scraper.js)
# This gets injected into the browser by Selenium's execute_script()
# ---------------------------------------------------------------------------
EXTRACT_JS = """
// --- Helper: parse numbers like "1,124,624" or "17M" or "1.128.112" ---
function parseNum(text) {
    if (!text) return 0;
    text = text.trim();

    // Handle K/M/B suffixes (e.g., "17M", "2.5K")
    var suffixMatch = text.match(/^([\\d.,]+)\\s*([KMB])$/i);
    if (suffixMatch) {
        var num = parseFloat(suffixMatch[1].replace(/,/g, ''));
        var mult = { K: 1000, M: 1000000, B: 1000000000 }[suffixMatch[2].toUpperCase()];
        return num * mult;
    }

    // Detect European format: "1.128.112" (dots as thousands, no comma)
    if (/^\\d{1,3}(\\.\\d{3}){2,}$/.test(text)) {
        return parseInt(text.replace(/\\./g, ''), 10);
    }

    // Standard format — commas are thousands separators
    return parseFloat(text.replace(/,/g, '')) || 0;
}

// --- Helper: find value by DOM label (most reliable for following/posts) ---
// Scans every element on the page looking for a label like "following",
// then checks sibling elements for a number
function findByLabel(labelText) {
    var allEls = document.querySelectorAll('*');
    for (var i = 0; i < allEls.length; i++) {
        var el = allEls[i];
        var t = el.innerText ? el.innerText.trim().toLowerCase() : '';
        if (t === labelText || t === labelText + 's') {
            var parent = el.parentElement;
            if (!parent) continue;
            var children = parent.children;
            for (var j = 0; j < children.length; j++) {
                var sib = children[j];
                if (sib === el) continue;
                var sibText = sib.innerText ? sib.innerText.trim() : '';
                if (sibText && /^[\\d.,]+[KMB]?$/.test(sibText)) {
                    return sibText;
                }
            }
        }
    }
    return null;
}

// --- Helper: find value from raw text (NUMBER before LABEL) ---
// Searches the full page text for patterns like "1,124,624\\nFollowers"
function findBeforeLabel(label) {
    var allText = document.body.innerText;
    var regex = new RegExp('([\\\\d.,]+[KMB]?)\\\\s*\\\\n\\\\s*' + label, 'i');
    var match = allText.match(regex);
    return match ? match[1] : null;
}

// --- Helper: extract daily growth from "Average followers per day" ---
function findDailyGrowth() {
    var allText = document.body.innerText;
    var match = allText.match(/([-+]?[\\d.,]+)\\s*\\n\\s*Average followers per day/i);
    return match ? parseNum(match[1]) : 0;
}

// --- Extract each metric using the best method per field ---
// Followers: regex (label_scan returns European format which is less reliable)
var followersRaw = findBeforeLabel('Followers');
var followers = parseNum(followersRaw);

// Following & Posts: DOM label scan (regex grabs weekly changes by mistake)
var followingRaw = findByLabel('following');
var following = parseNum(followingRaw);

var postsRaw = findByLabel('post');
var postsCount = parseNum(postsRaw);

// Avg Likes & Comments: both methods agree, try label first then regex
var avgLikesRaw = findByLabel('avg like') || findBeforeLabel('Avg likes');
var avgLikes = parseNum(avgLikesRaw);

var avgCommentsRaw = findByLabel('avg comment') || findBeforeLabel('Avg comments');
var avgComments = parseNum(avgCommentsRaw);

// Engagement Rate: calculated (site locks it behind login)
var engagementRate = followers > 0
    ? Math.round(((avgLikes + avgComments) / followers) * 10000) / 100
    : 0;

// Growth Rate: convert daily followers change to monthly percentage
var dailyGrowth = findDailyGrowth();
var growthRate = followers > 0
    ? Math.round((dailyGrowth * 30 / followers) * 1000) / 10
    : 0;

// Username: from URL path
var username = window.location.pathname.split('/').pop();

return {
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
"""


def validate_result(data: dict) -> bool:
    """
    Check if the extracted data looks valid.
    Returns True if we got meaningful data, False if extraction failed.
    """
    if not data:
        return False
    if data.get("followers", 0) == 0:
        return False
    return True


def clean_result(data: dict, username: str) -> dict:
    """
    Post-process the raw JS result:
    - Override username from the function argument (more reliable than URL parsing)
    - Ensure all expected fields exist
    """
    expected_fields = {
        "username": username,
        "followers": 0,
        "following": 0,
        "posts_count": 0,
        "engagement_rate": 0,
        "avg_likes": 0,
        "avg_comments": 0,
        "growth_rate": 0,
        "authenticity_score": 0,
    }

    # Fill in any missing fields with defaults
    for key, default in expected_fields.items():
        if key not in data:
            data[key] = default

    # Always use the username we were asked to scrape
    data["username"] = username

    return data
