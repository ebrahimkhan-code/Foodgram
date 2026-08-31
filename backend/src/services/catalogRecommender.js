/**
 * catalogRecommender.js
 *
 * A lightweight, dependency-free recommender that reads the enriched menu
 * catalog (menu_dataset_enriched_claude_FINAL.csv) directly in Node and ranks
 * dishes against a user's taste preferences.
 *
 * Why this exists: the "real" member1 model runs in the Python/Flask service.
 * When that service is offline (or its venv deps aren't installed yet), we
 * still want recommendations to come from the SAME enriched CSV — complete
 * with real product images (image_url), price and restaurant — instead of the
 * generic Postgres `foods` table. So this module powers the fallback path and
 * guarantees the recommendation cards always have images.
 */

const fs = require('fs');
const path = require('path');

// Candidate locations for the enriched catalog CSV (first hit wins).
const CSV_CANDIDATES = [
    path.join(__dirname, '..', '..', 'member1-recommender', 'data', 'menu_dataset_enriched_claude_FINAL.csv'),
    path.join(__dirname, '..', '..', '..', 'member1-recommender', 'data', 'menu_dataset_enriched_claude_FINAL.csv'),
];

// Attributes we match a dish against the taste profile on.
const MATCH_ATTRS = ['cuisine', 'protein', 'flavor', 'spice_level', 'meal_type', 'base'];

let _catalog = null; // cached array of row objects

// --- Minimal RFC-4180 CSV parser (handles quoted fields, commas & "" escapes) ---
function parseCSV(text) {
    const rows = [];
    let field = '';
    let row = [];
    let inQuotes = false;

    for (let i = 0; i < text.length; i++) {
        const c = text[i];
        if (inQuotes) {
            if (c === '"') {
                if (text[i + 1] === '"') { field += '"'; i++; } // escaped quote
                else { inQuotes = false; }
            } else { field += c; }
        } else if (c === '"') {
            inQuotes = true;
        } else if (c === ',') {
            row.push(field); field = '';
        } else if (c === '\n') {
            row.push(field); rows.push(row); row = []; field = '';
        } else if (c === '\r') {
            // ignore; \n handles the line break
        } else {
            field += c;
        }
    }
    if (field.length > 0 || row.length > 0) { row.push(field); rows.push(row); }
    return rows;
}

function loadCatalog() {
    if (_catalog) return _catalog;

    let csvPath = null;
    for (const candidate of CSV_CANDIDATES) {
        if (fs.existsSync(candidate)) { csvPath = candidate; break; }
    }
    if (!csvPath) {
        console.error('⚠️  catalogRecommender: CSV not found in', CSV_CANDIDATES);
        _catalog = [];
        return _catalog;
    }

    const raw = fs.readFileSync(csvPath, 'utf8');
    const rows = parseCSV(raw);
    if (rows.length < 2) { _catalog = []; return _catalog; }

    const header = rows[0].map(h => h.trim());
    _catalog = rows.slice(1)
        .filter(r => r.length > 1)
        .map(r => {
            const obj = {};
            header.forEach((key, idx) => { obj[key] = r[idx] !== undefined ? r[idx] : ''; });
            return obj;
        });

    console.log(`✅ catalogRecommender: loaded ${_catalog.length} dishes from ${path.basename(csvPath)}`);
    return _catalog;
}

const norm = v => String(v == null ? '' : v).trim().toLowerCase();
const toNumber = (v, d = 0) => {
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : d;
};

// Build an {attribute: {value: weight}} preference map from raw game answers.
function answersToPreferences(answers = []) {
    const prefs = {};
    (answers || []).forEach(a => {
        if (!a || !a.attribute || !a.value) return;
        const attr = norm(a.attribute);
        const val = norm(a.value);
        if (!MATCH_ATTRS.includes(attr) || !val || val === 'skip') return;
        const weight = typeof a.preference === 'number' ? a.preference : 1;
        prefs[attr] = prefs[attr] || {};
        prefs[attr][val] = (prefs[attr][val] || 0) + weight;
    });
    return prefs;
}

// Extract the per-attribute weight maps out of a member1-style Taste DNA object.
function dnaToPreferences(tasteDNA = {}) {
    const prefs = {};
    if (!tasteDNA || typeof tasteDNA !== 'object') return prefs;
    MATCH_ATTRS.forEach(attr => {
        const map = tasteDNA[attr];
        if (map && typeof map === 'object' && Object.keys(map).length) {
            prefs[attr] = {};
            Object.entries(map).forEach(([k, v]) => { prefs[attr][norm(k)] = toNumber(v, 0); });
        }
    });
    return prefs;
}

function formatRecord(row, score, reason) {
    const s = Math.max(0, Math.min(0.99, score));
    const confidence = s >= 0.66 ? 'high' : (s >= 0.4 ? 'medium' : 'low');
    return {
        food_id: row.food_id || row.id || row.name,
        name: row.name || 'Dish',
        description: row.description || '',
        cuisine: row.cuisine || 'Various',
        protein: row.protein || '',
        flavor: row.flavor || '',
        spice_level: row.spice_level || '',
        meal_type: row.meal_type || '',
        category: row.category || '',
        restaurant: row.restaurant || '',
        price: toNumber(row.price, 0),
        currency: row.currency || 'PKR',
        rating: toNumber(row.rating, 0),
        image_url: row.image_url || '',
        score: Math.round(s * 10000) / 10000,
        confidence,
        reason: reason || 'Recommended based on your taste profile',
    };
}

// Rank the whole catalog for a preference map and return the top `limit`
// dishes (deduped by dish name). Empty prefs => top-rated "popular picks".
function recommend(prefs = {}, limit = 12) {
    const catalog = loadCatalog();
    if (!catalog.length) return [];

    const activeAttrs = MATCH_ATTRS.filter(a => prefs[a] && Object.keys(prefs[a]).length);
    const BASE = 0.35;

    const scored = catalog.map(row => {
        let matched = 0;
        activeAttrs.forEach(attr => {
            const foodVal = norm(row[attr]);
            if (foodVal && prefs[attr][foodVal] !== undefined) matched += 1;
        });
        const frac = activeAttrs.length ? matched / activeAttrs.length : 0;
        const rating = toNumber(row.rating, 0);
        let score = BASE + (1 - BASE) * frac;      // 0.35 .. 1.0 by taste match
        score += Math.max(0, (rating - 4.0)) * 0.02; // tiny quality nudge
        return { row, score, rating };
    });

    scored.sort((a, b) => (b.score - a.score) || (b.rating - a.rating));

    // Dedupe by dish name so we don't show the same item many times.
    const seen = new Set();
    const out = [];
    for (const item of scored) {
        const key = norm(item.row.name);
        if (key && seen.has(key)) continue;
        seen.add(key);
        out.push(formatRecord(item.row, item.score));
        if (out.length >= limit) break;
    }
    return out;
}

// ---- Free-text search over the catalog (fallback for Member 2 /ask & /search) ----

// Words that carry no dish signal — dropped before keyword matching so they
// don't create spurious matches.
const STOPWORDS = new Set([
    'a', 'an', 'the', 'me', 'my', 'i', 'is', 'it', 'to', 'of', 'and', 'or', 'for',
    'with', 'some', 'good', 'nice', 'best', 'tasty', 'dish', 'dishes', 'food',
    'foods', 'option', 'options', 'please', 'find', 'show', 'want', 'looking',
    'something', 'give', 'that', 'under', 'below', 'over', 'above', 'less', 'than',
    'rs', 'pkr', 'price', 'around', 'cheap', 'budget', 'meal',
]);

// Keyword + light-intent search over the enriched catalog. Returns ranked
// formatRecord() objects (same shape as recommend()), so the frontend renders
// them identically. Understands a few natural hints: veg / non-veg, spicy,
// sweet/dessert, and price limits ("under Rs. 800", "above 500").
function searchCatalog(query, limit = 6) {
    const catalog = loadCatalog();
    if (!catalog.length) return [];

    const q = norm(query);
    if (!q) return [];

    // Price constraints, e.g. "under Rs. 800", "above 500".
    let maxPrice = null;
    let minPrice = null;
    const under = q.match(/(?:under|below|less than|up ?to|<)\s*(?:rs\.?|pkr)?\s*(\d{2,5})/);
    if (under) maxPrice = parseInt(under[1], 10);
    const over = q.match(/(?:over|above|more than|>)\s*(?:rs\.?|pkr)?\s*(\d{2,5})/);
    if (over) minPrice = parseInt(over[1], 10);

    // Light intent detection.
    const wantsVeg = /\b(veg|vegetarian|vegan)\b/.test(q) && !/non[-\s]?veg/.test(q);
    const wantsNonVeg = /non[-\s]?veg/.test(q) || /\b(meat|chicken|beef|mutton|fish|lamb)\b/.test(q);
    const wantsSpicy = /\b(spicy|hot|chilli|chili)\b/.test(q);
    const wantsSweet = /\b(sweet|dessert|desserts)\b/.test(q);

    const tokens = q.split(/[^a-z0-9]+/)
        .filter(t => t.length > 1 && !STOPWORDS.has(t) && !/^\d+$/.test(t));

    const scored = catalog.map(row => {
        const name = norm(row.name);
        const blob = [
            row.name, row.description, row.cuisine, row.protein, row.flavor,
            row.spice_level, row.meal_type, row.category, row.dietary_tags,
            row.restaurant, row.veg_status, row.base, row.food_type,
        ].map(norm).join(' ');

        let score = 0;
        tokens.forEach(t => {
            if (name.includes(t)) score += 3;          // name hit weighs most
            else if (blob.includes(t)) score += 1;
        });

        const veg = norm(row.veg_status);
        const isVeg = veg.includes('veg') && !veg.includes('non');
        if (wantsVeg) score += isVeg ? 2 : -3;
        if (wantsNonVeg && veg && !isVeg) score += 2;

        const spice = norm(row.spice_level);
        if (wantsSpicy && (spice.includes('spicy') || spice.includes('hot') || spice.includes('high'))) score += 2;

        if (wantsSweet && (norm(row.flavor).includes('sweet') ||
            norm(row.category).includes('dessert') || norm(row.food_type).includes('dessert'))) score += 2;

        const price = toNumber(row.price, 0);
        let priceOk = true;
        if (maxPrice != null && price > 0 && price > maxPrice) priceOk = false;
        if (minPrice != null && price > 0 && price < minPrice) priceOk = false;

        return { row, score, rating: toNumber(row.rating, 0), priceOk };
    });

    let candidates = scored.filter(s => s.priceOk);
    // If anything actually matched the words/intent, drop the zero-signal noise;
    // otherwise fall back to the (price-filtered) top-rated dishes.
    if (candidates.some(s => s.score > 0)) {
        candidates = candidates.filter(s => s.score > 0);
    }
    candidates.sort((a, b) => (b.score - a.score) || (b.rating - a.rating));

    const seen = new Set();
    const out = [];
    for (const item of candidates) {
        const key = norm(item.row.name);
        if (key && seen.has(key)) continue;
        seen.add(key);
        const s = item.score > 0 ? Math.min(0.95, 0.5 + item.score * 0.07) : 0.42;
        out.push(formatRecord(item.row, s, 'Matches your search'));
        if (out.length >= limit) break;
    }
    return out;
}

// Look up a single dish by its catalog food_id (or name). Returns a
// formatRecord() object or null. Used to answer "explain this dish" from the
// CSV when Member 2 is offline.
function getById(foodId) {
    const catalog = loadCatalog();
    if (!catalog.length || !foodId) return null;
    const id = norm(foodId);
    const row = catalog.find(r => norm(r.food_id) === id || norm(r.id) === id || norm(r.name) === id);
    return row ? formatRecord(row, 0.6, row.description || '') : null;
}

// ---- Photo "this or that" game helpers ----

// Non-mutating Fisher-Yates shuffle.
function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

// Compact dish object for the photo game. Must carry the image plus the
// attributes we turn into Taste DNA answers when a dish is chosen.
function toGameDish(row) {
    return {
        food_id: row.food_id || row.id || row.name,
        name: row.name || 'Dish',
        description: row.description || '',
        image_url: row.image_url || '',
        restaurant: row.restaurant || '',
        cuisine: row.cuisine || '',
        protein: row.protein || '',
        flavor: row.flavor || '',
        spice_level: row.spice_level || '',
        meal_type: row.meal_type || '',
        base: row.base || '',
        price: toNumber(row.price, 0),
        currency: row.currency || 'PKR',
        rating: toNumber(row.rating, 0),
    };
}

// Build `n` "this or that" rounds. Each round is two DISTINCT dishes that both
// have real images; partners are chosen to contrast on cuisine/protein so the
// pick is meaningful. No dish repeats across the returned rounds.
function getPhotoRounds(n = 8) {
    const catalog = loadCatalog();
    const seen = new Set();
    const withImages = [];
    for (const row of catalog) {
        const img = String(row.image_url || '').trim();
        const key = norm(row.name);
        if (!img || !key || seen.has(key)) continue;
        seen.add(key);
        withImages.push(row);
    }

    const deck = shuffle(withImages);
    const rounds = [];
    let i = 0;
    for (let r = 0; r < n && i + 1 < deck.length; r++) {
        const leftRow = deck[i++];
        // Find a contrasting partner within a small look-ahead window.
        let j = i;
        for (let k = i; k < Math.min(i + 25, deck.length); k++) {
            if (norm(deck[k].cuisine) !== norm(leftRow.cuisine) ||
                norm(deck[k].protein) !== norm(leftRow.protein)) {
                j = k;
                break;
            }
        }
        const rightRow = deck[j];
        // Pull rightRow to the current slot so it's consumed and not reused.
        deck[j] = deck[i];
        deck[i] = rightRow;
        i++;
        rounds.push({ round: r + 1, left: toGameDish(leftRow), right: toGameDish(rightRow) });
    }
    return rounds;
}

module.exports = {
    recommend,
    searchCatalog,
    getById,
    answersToPreferences,
    dnaToPreferences,
    loadCatalog,
    getCount: () => loadCatalog().length,
    getPhotoRounds,
};
