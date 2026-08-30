const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

async function runSchema() {
    try {
        console.log('📋 Running schema...');
        const schemaPath = path.join(__dirname, 'schema.sql');
        
        if (!fs.existsSync(schemaPath)) {
            console.log('❌ schema.sql not found!');
            return false;
        }

        const schema = fs.readFileSync(schemaPath, 'utf8');
        await pool.query(schema);
        console.log('✅ Schema applied successfully!');
        return true;
    } catch (error) {
        console.error('❌ Schema error:', error.message);
        return false;
    }
}

async function seedDatabase() {
    try {
        console.log('🌱 Seeding database...');

        // Run schema first
        const schemaApplied = await runSchema();
        if (!schemaApplied) {
            console.log('⛔ Aborting seed.');
            return;
        }

        // Check if foods table exists and has data
        const tableCheck = await pool.query(`
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'foods'
            );
        `);

        if (!tableCheck.rows[0].exists) {
            console.log('❌ Table "foods" does not exist.');
            return;
        }

        // Clear existing foods
        await pool.query('DELETE FROM foods');
        console.log('🗑️ Cleared existing foods');

        // Demo foods data
        const demoFoods = [
            {
                id: 'food-1',
                name: 'Spicy Chicken Pasta',
                description: 'Bold fusion of Italian and Asian flavors with a spicy kick',
                ingredients: ['chicken breast', 'penne pasta', 'red chili flakes', 'garlic', 'tomato sauce', 'basil'],
                cuisine: 'Italian-Asian Fusion',
                meal_type: 'Dinner',
                price: 16.99,
                image_url: 'https://via.placeholder.com/300x200/ff6b35/fff?text=Spicy+Pasta',
                metadata: JSON.stringify({ spice_level: 4, prep_time: 30, popularity: 4.5 })
            },
            {
                id: 'food-2',
                name: 'Truffle Mushroom Risotto',
                description: 'Creamy and earthy Italian classic with truffle oil',
                ingredients: ['arborio rice', 'porcini mushrooms', 'truffle oil', 'parmesan cheese', 'vegetable broth'],
                cuisine: 'Italian',
                meal_type: 'Dinner',
                price: 18.99,
                image_url: 'https://via.placeholder.com/300x200/8b7355/fff?text=Risotto',
                metadata: JSON.stringify({ spice_level: 1, prep_time: 45, popularity: 4.8 })
            },
            {
                id: 'food-3',
                name: 'Korean BBQ Tacos',
                description: 'Sweet and savory fusion street food with kimchi',
                ingredients: ['pork belly', 'corn tortilla', 'kimchi', 'gochujang sauce', 'sesame seeds'],
                cuisine: 'Korean-Mexican',
                meal_type: 'Lunch',
                price: 12.99,
                image_url: 'https://via.placeholder.com/300x200/d4203a/fff?text=Korean+Tacos',
                metadata: JSON.stringify({ spice_level: 5, prep_time: 25, popularity: 4.9 })
            },
            {
                id: 'food-4',
                name: 'Mediterranean Bowl',
                description: 'Fresh and healthy Mediterranean grain bowl',
                ingredients: ['quinoa', 'chickpeas', 'cucumber', 'tomato', 'feta cheese', 'tahini dressing'],
                cuisine: 'Mediterranean',
                meal_type: 'Lunch',
                price: 13.99,
                image_url: 'https://via.placeholder.com/300x200/2e8b57/fff?text=Mediterranean',
                metadata: JSON.stringify({ spice_level: 2, prep_time: 20, popularity: 4.3 })
            },
            {
                id: 'food-5',
                name: 'Miso Glazed Salmon',
                description: 'Japanese-inspired salmon with miso glaze and vegetables',
                ingredients: ['salmon fillet', 'white miso', 'soy sauce', 'mirin', 'broccoli', 'rice'],
                cuisine: 'Japanese',
                meal_type: 'Dinner',
                price: 22.99,
                image_url: 'https://via.placeholder.com/300x200/de6b28/fff?text=Miso+Salmon',
                metadata: JSON.stringify({ spice_level: 3, prep_time: 35, popularity: 4.7 })
            },
            {
                id: 'food-6',
                name: 'Mango Avocado Sushi',
                description: 'Fresh and vibrant sushi rolls with tropical twist',
                ingredients: ['sushi rice', 'nori', 'avocado', 'mango', 'cucumber', 'cream cheese'],
                cuisine: 'Japanese',
                meal_type: 'Light Meal',
                price: 14.99,
                image_url: 'https://via.placeholder.com/300x200/f4a460/fff?text=Sushi',
                metadata: JSON.stringify({ spice_level: 1, prep_time: 40, popularity: 4.6 })
            },
            {
                id: 'food-7',
                name: 'Butter Chicken Curry',
                description: 'Rich and creamy Indian curry with tender chicken',
                ingredients: ['chicken thigh', 'tomato puree', 'cream', 'butter', 'garam masala', 'ginger garlic'],
                cuisine: 'Indian',
                meal_type: 'Dinner',
                price: 17.99,
                image_url: 'https://via.placeholder.com/300x200/d2691e/fff?text=Butter+Chicken',
                metadata: JSON.stringify({ spice_level: 4, prep_time: 50, popularity: 4.9 })
            },
            {
                id: 'food-8',
                name: 'Thai Green Curry',
                description: 'Aromatic and spicy Thai curry with coconut milk',
                ingredients: ['chicken breast', 'coconut milk', 'green curry paste', 'eggplant', 'basil', 'bamboo shoots'],
                cuisine: 'Thai',
                meal_type: 'Dinner',
                price: 16.99,
                image_url: 'https://via.placeholder.com/300x200/228b22/fff?text=Thai+Curry',
                metadata: JSON.stringify({ spice_level: 5, prep_time: 35, popularity: 4.7 })
            },
            {
                id: 'food-9',
                name: 'Caprese Flatbread',
                description: 'Fresh Italian flatbread with tomato, mozzarella, and basil',
                ingredients: ['flatbread', 'tomato', 'fresh mozzarella', 'basil', 'balsamic glaze'],
                cuisine: 'Italian',
                meal_type: 'Lunch',
                price: 11.99,
                image_url: 'https://via.placeholder.com/300x200/dc143c/fff?text=Caprese',
                metadata: JSON.stringify({ spice_level: 1, prep_time: 15, popularity: 4.4 })
            },
            {
                id: 'food-10',
                name: 'Chocolate Lava Cake',
                description: 'Decadent dessert with warm chocolate center',
                ingredients: ['dark chocolate', 'butter', 'eggs', 'sugar', 'flour', 'vanilla'],
                cuisine: 'Dessert',
                meal_type: 'Dessert',
                price: 8.99,
                image_url: 'https://via.placeholder.com/300x200/8b4513/fff?text=Lava+Cake',
                metadata: JSON.stringify({ spice_level: 0, prep_time: 25, popularity: 4.8 })
            },
            {
                id: 'food-11',
                name: 'Veggie Burger',
                description: 'Plant-based burger with all the fixings',
                ingredients: ['black beans', 'quinoa', 'mushrooms', 'onion', 'garlic', 'whole wheat bun'],
                cuisine: 'American',
                meal_type: 'Lunch',
                price: 13.99,
                image_url: 'https://via.placeholder.com/300x200/228b22/fff?text=Veggie+Burger',
                metadata: JSON.stringify({ spice_level: 2, prep_time: 30, popularity: 4.2 })
            },
            {
                id: 'food-12',
                name: 'Pineapple Fried Rice',
                description: 'Sweet and savory Thai-style fried rice in pineapple shell',
                ingredients: ['jasmine rice', 'pineapple', 'shrimp', 'cashews', 'egg', 'curry powder'],
                cuisine: 'Thai',
                meal_type: 'Dinner',
                price: 15.99,
                image_url: 'https://via.placeholder.com/300x200/ffa500/fff?text=Fried+Rice',
                metadata: JSON.stringify({ spice_level: 3, prep_time: 30, popularity: 4.5 })
            }
        ];

        // Insert each food
        for (const food of demoFoods) {
            const query = `
                INSERT INTO foods (
                    id, name, description, ingredients, 
                    cuisine, meal_type, price, image_url, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    ingredients = EXCLUDED.ingredients,
                    cuisine = EXCLUDED.cuisine,
                    meal_type = EXCLUDED.meal_type,
                    price = EXCLUDED.price,
                    image_url = EXCLUDED.image_url,
                    metadata = EXCLUDED.metadata
            `;

            await pool.query(query, [
                food.id,
                food.name,
                food.description,
                food.ingredients,
                food.cuisine,
                food.meal_type,
                food.price,
                food.image_url,
                food.metadata
            ]);

            console.log(`✅ Inserted: ${food.name} ($${food.price})`);
        }

        console.log('🎉 Database seeding completed!');
        
        // Verification
        const result = await pool.query('SELECT COUNT(*) FROM foods');
        console.log(`🔍 Verification: ${result.rows[0].count} foods in database`);

        // Show sample foods
        const sample = await pool.query('SELECT id, name, cuisine, price FROM foods LIMIT 3');
        console.log('\n📋 Sample foods:');
        sample.rows.forEach(row => {
            console.log(`   - ${row.id}: ${row.name} (${row.cuisine}) - $${row.price}`);
        });

    } catch (error) {
        console.error('❌ Seeding failed:', error);
        if (error.code === '42P01') {
            console.log('💡 Hint: Table "foods" doesn\'t exist. Run schema.sql first.');
        }
    } finally {
        await pool.end();
    }
}

// Run the seed
if (require.main === module) {
    seedDatabase();
}

module.exports = { seedDatabase };