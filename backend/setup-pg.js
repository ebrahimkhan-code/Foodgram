const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

// Configuration
const config = {
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    password: process.env.DB_PASSWORD || 'postgres', // Change this!
    port: parseInt(process.env.DB_PORT) || 5432,
    database: 'postgres'
};

async function setup() {
    console.log('🚀 Setting up PostgreSQL...\n');

    // Test if PostgreSQL is running
    const pool = new Pool(config);
    
    try {
        // Try to connect
        await pool.connect();
        console.log('✅ PostgreSQL is running!');
    } catch (error) {
        console.log('❌ PostgreSQL is not running or not installed.');
        console.log('\n📝 Please:');
        console.log('1. Install PostgreSQL from: https://www.postgresql.org/download/windows/');
        console.log('2. Start PostgreSQL service');
        console.log('3. Update .env with your credentials');
        return;
    }

    // Create database
    try {
        await pool.query(`CREATE DATABASE "${process.env.DB_NAME || 'foodgram'}"`);
        console.log('✅ Database created!');
    } catch (err) {
        if (err.code === '42P04') {
            console.log('ℹ️ Database already exists');
        } else {
            console.log('❌ Error creating database:', err.message);
        }
    }

    await pool.end();

    // Now connect to the new database
    const appPool = new Pool({
        ...config,
        database: process.env.DB_NAME || 'foodgram'
    });

    // Read and run schema
    try {
        const schemaPath = path.join(__dirname, 'src', 'database', 'schema.sql');
        if (fs.existsSync(schemaPath)) {
            const schema = fs.readFileSync(schemaPath, 'utf8');
            await appPool.query(schema);
            console.log('✅ Schema applied!');
        } else {
            console.log('⚠️ No schema.sql found, skipping...');
        }
    } catch (error) {
        console.log('❌ Error applying schema:', error.message);
    }

    await appPool.end();

    console.log('\n🎉 Setup complete!');
    console.log('📊 Database: foodgram');
    console.log('👤 User: postgres');
    console.log('🔐 Password: (your password)');
    console.log('\nRun: npm run seed');
}

setup();