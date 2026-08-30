const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, 'foodgram.db');
const db = new sqlite3.Database(dbPath);

// Create tables
db.serialize(() => {
    // Users table
    db.run(`
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            session_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            taste_dna TEXT
        )
    `);

    // Sessions table
    db.run(`
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            session_id TEXT UNIQUE,
            taste_dna TEXT,
            game_responses TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            is_converted INTEGER DEFAULT 0
        )
    `);

    // Foods table
    db.run(`
        CREATE TABLE IF NOT EXISTS foods (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            ingredients TEXT,
            cuisine TEXT,
            meal_type TEXT,
            image_url TEXT,
            metadata TEXT
        )
    `);

    // Insert demo foods
    const foods = [
        ['food-1', 'Spicy Chicken Pasta', 'Bold fusion of Italian and Asian flavors', 
         '["chicken","pasta","spices"]', 'Italian-Asian', 'Dinner', 
         'https://via.placeholder.com/300x200/ff6b35/fff?text=Spicy+Pasta', '{"spice":4}'],
        // Add more foods...
    ];

    const stmt = db.prepare(`
        INSERT OR IGNORE INTO foods (id, name, description, ingredients, cuisine, meal_type, image_url, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    foods.forEach(food => stmt.run(food));
    stmt.finalize();

    console.log('✅ SQLite database created with demo data!');
    console.log(`📁 Database file: ${dbPath}`);
});

db.close();