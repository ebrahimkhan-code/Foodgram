const { Pool } = require('pg');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config();

console.log('🔍 Environment variables loaded:');
console.log(`📊 DB_HOST: ${process.env.DB_HOST || 'localhost'}`);
console.log(`📊 DB_USER: ${process.env.DB_USER || 'postgres'}`);
console.log(`📊 DB_NAME: ${process.env.DB_NAME || 'foodgram'}`);
console.log(`📊 DB_PORT: ${process.env.DB_PORT || 5432}`);

// Configuration
const config = {
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    password: process.env.DB_PASSWORD || 'postgres',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: 'postgres', // Connect to default database first
    connectionTimeoutMillis: 5000,
};

console.log('\n🔌 Attempting to connect to PostgreSQL...');

// Create pool
const pool = new Pool(config);

async function createDatabase() {
    let client;
    
    try {
        // Try to connect
        client = await pool.connect();
        console.log('✅ Connected to PostgreSQL successfully!');
        console.log(`📡 PostgreSQL version: ${client.serverVersion}`);
        client.release();

        const dbName = process.env.DB_NAME || 'foodgram';

        // Check if database exists
        console.log(`\n🔍 Checking if database "${dbName}" exists...`);
        const checkResult = await pool.query(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            [dbName]
        );

        if (checkResult.rows.length === 0) {
            // Create database
            console.log(`📝 Creating database "${dbName}"...`);
            await pool.query(`CREATE DATABASE "${dbName}"`);
            console.log(`✅ Database "${dbName}" created successfully!`);
        } else {
            console.log(`ℹ️ Database "${dbName}" already exists`);
        }

        console.log('\n🎉 Database setup complete!');
        console.log('📊 You can now run: npm run seed');

    } catch (error) {
        console.error('\n❌ Error:', error.message);
        
        if (error.code === 'ECONNREFUSED') {
            console.log('\n📝 PostgreSQL is not running. Please:');
            console.log('1. Check if PostgreSQL is installed');
            console.log('2. Start PostgreSQL service:');
            console.log('   - Press Win + R, type: services.msc');
            console.log('   - Find "postgresql" service');
            console.log('   - Right-click → Start');
            console.log('3. Check your .env file credentials');
        } else if (error.code === '28P01') {
            console.log('\n📝 Invalid password. Check your .env file:');
            console.log(`   DB_PASSWORD=${process.env.DB_PASSWORD || 'not set'}`);
            console.log('   Try setting it to: postgres');
        } else if (error.code === '3D000') {
            console.log('\n📝 Database does not exist. Creating...');
            // Try to create database without connecting to it first
            try {
                await pool.query(`CREATE DATABASE "${process.env.DB_NAME || 'foodgram'}"`);
                console.log('✅ Database created!');
            } catch (createError) {
                console.log('❌ Could not create database:', createError.message);
            }
        } else {
            console.log('\n📝 Full error details:', error);
        }
    } finally {
        await pool.end();
        console.log('\n🔌 Connection closed.');
    }
}

// Run the function
if (require.main === module) {
    createDatabase();
}

module.exports = { createDatabase };