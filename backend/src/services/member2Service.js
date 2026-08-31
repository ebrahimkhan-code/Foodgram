// Member 2 (Data / RAG / LLM) service client.
//
// Talks to the FastAPI service in member2_data_rag_llm/api_server.py over HTTP,
// mirroring the pattern of member1Service.js. Member 2 provides:
//   • /recommendations/explain — a grounded, natural-language reason for a
//     specific recommended dish (used to enrich Member 1's ranked cards)
//   • /search                  — semantic search over the food knowledge base
//   • /ask                     — RAG question answering ("what's a good spicy
//     vegetarian option?")
//   • /ask-specific            — a question about one known dish (food detail)
//   • /health                  — component readiness
//
// Uses Node 18+ global fetch (no node-fetch dependency) with an AbortController
// timeout, because native fetch ignores node-fetch's `timeout` option.
//
// The whole service is treated as OPTIONAL: every call throws on failure and the
// callers in server.js wrap these in best-effort try/catch so recommendations,
// search and Q&A degrade gracefully when Member 2 is offline or its LLM key is
// missing. Member 2 lives on its own port (default 8001) so it does not collide
// with Member 1's Flask service on 8000.

class Member2Service {
    constructor() {
        this.baseURL = process.env.MEMBER2_API_URL || 'http://localhost:8001';
        this.timeout = parseInt(process.env.MEMBER2_TIMEOUT) || 12000;
        // Explanations call an LLM per dish and are the slow path; give them a
        // tighter budget so a slow LLM never stalls the recommendations request.
        this.explainTimeout = parseInt(process.env.MEMBER2_EXPLAIN_TIMEOUT) || 6000;
        // Feature flag: set MEMBER2_ENABLED=false to fully bypass Member 2.
        this.enabled = String(process.env.MEMBER2_ENABLED || 'true').toLowerCase() !== 'false';
    }

    isEnabled() {
        return this.enabled;
    }

    async _call(endpoint, method = 'GET', body = null, timeoutMs = null) {
        const url = `${this.baseURL}${endpoint}`;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs || this.timeout);

        const options = {
            method,
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal,
        };
        if (body) options.body = JSON.stringify(body);

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`Member2 API error: ${response.status} - ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error(`Member2 API timeout after ${timeoutMs || this.timeout}ms: ${method} ${endpoint}`);
            }
            throw error;
        } finally {
            clearTimeout(timer);
        }
    }

    // Member 1 → Member 2: explain a specific recommended dish.
    // Returns { explanation, reasoning, retrieved_document, grounded, ... }.
    async explainRecommendation(foodId, mlScore, userTasteSummary, confidenceClass = null) {
        // Clamp score into [0,1] — the FastAPI model validates this range and
        // 400s otherwise. Member 1 / the CSV scorer occasionally emit >1.
        let score = Number(mlScore);
        if (!Number.isFinite(score)) score = 0.5;
        score = Math.max(0, Math.min(1, score));

        return this._call('/recommendations/explain', 'POST', {
            food_id: foodId,
            ml_score: score,
            user_taste_summary: userTasteSummary || 'General taste profile',
            confidence_class: confidenceClass || undefined,
        }, this.explainTimeout);
    }

    // Member 3 → Member 2: semantic search. `filters` is a flat object of the
    // optional query params the API accepts (veg_status, food_type, category,
    // price_min, price_max).
    async search(query, filters = {}, topK = 6) {
        const params = new URLSearchParams();
        params.set('query', query);
        params.set('top_k', String(topK));
        for (const [k, v] of Object.entries(filters || {})) {
            if (v !== undefined && v !== null && v !== '') params.set(k, String(v));
        }
        return this._call(`/search?${params.toString()}`, 'GET');
    }

    // Member 3 → Member 2: open-ended RAG question answering.
    async ask(query, filters = null, topK = 3) {
        return this._call('/ask', 'POST', {
            query,
            filters: filters || undefined,
            top_k: topK,
        });
    }

    // Member 3 → Member 2: a question about one specific dish (food detail page).
    // NOTE: the FastAPI route takes food_id + query as QUERY params, not a body.
    async askSpecific(foodId, query) {
        const params = new URLSearchParams({ food_id: foodId, query });
        return this._call(`/ask-specific?${params.toString()}`, 'POST');
    }

    async healthCheck() {
        return this._call('/health', 'GET', null, 3000);
    }
}

module.exports = new Member2Service();
