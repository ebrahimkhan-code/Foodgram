// Uses Node 18+ global fetch (no node-fetch dependency required).
// A timeout is applied via AbortController because native fetch ignores the
// non-standard `timeout` option that node-fetch supported.

class Member1Service {
    constructor() {
        this.baseURL = process.env.MEMBER1_API_URL || 'http://localhost:8000';
        this.timeout = parseInt(process.env.MEMBER1_TIMEOUT) || 15000;
    }

    async _call(endpoint, method = 'GET', data = null) {
        const url = `${this.baseURL}${endpoint}`;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.timeout);

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            signal: controller.signal,
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            console.log(`📡 Calling Member1: ${method} ${endpoint}`);
            const response = await fetch(url, options);

            if (!response.ok) {
                throw new Error(`Member1 API error: ${response.status} - ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error(`❌ Member1 API timeout after ${this.timeout}ms: ${method} ${endpoint}`);
                throw new Error(`Member1 API timeout after ${this.timeout}ms`);
            }
            console.error(`❌ Member1 API error: ${error.message}`);
            throw error;
        } finally {
            clearTimeout(timer);
        }
    }

    // Generate Taste DNA from game answers
    async generateTasteDNA(answers) {
        return this._call('/api/taste-dna/generate', 'POST', { answers });
    }

    // Update Taste DNA based on interaction
    async updateTasteDNA(tasteDNA, interaction) {
        return this._call('/api/taste-dna/update', 'POST', {
            taste_dna: tasteDNA,
            interaction
        });
    }

    // Get recommendations
    async getRecommendations(tasteDNA, history = [], context = {}, limit = 10) {
        return this._call('/api/recommendations', 'POST', {
            taste_dna: tasteDNA,
            history,
            context,
            limit
        });
    }

    // Get exploration recommendations
    async getExplorationRecommendations(tasteDNA, history = [], limit = 8) {
        return this._call('/api/recommendations/explore', 'POST', {
            taste_dna: tasteDNA,
            history,
            limit
        });
    }

    // Get game questions
    async getGameQuestions() {
        return this._call('/api/game/questions', 'GET');
    }

    // Health check
    async healthCheck() {
        return this._call('/health', 'GET');
    }
}

module.exports = new Member1Service();