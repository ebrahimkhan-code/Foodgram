-- backend/src/database/seed.sql

-- Clear existing data
TRUNCATE TABLE foods CASCADE;

-- Insert demo foods
INSERT INTO foods (id, name, description, ingredients, cuisine, meal_type, image_url, metadata) VALUES
('food-1', 'Spicy Chicken Pasta', 'Bold fusion of Italian and Asian flavors with a spicy kick', 
 ARRAY['chicken breast', 'penne pasta', 'red chili flakes', 'garlic', 'tomato sauce', 'basil'], 
 'Italian-Asian Fusion', 'Dinner', 
 'https://via.placeholder.com/300x200/ff6b35/fff?text=Spicy+Pasta',
 '{"spice_level": 4, "prep_time": 30, "popularity": 4.5}'),

('food-2', 'Truffle Mushroom Risotto', 'Creamy and earthy Italian classic with truffle oil', 
 ARRAY['arborio rice', 'porcini mushrooms', 'truffle oil', 'parmesan cheese', 'vegetable broth'], 
 'Italian', 'Dinner',
 'https://via.placeholder.com/300x200/8b7355/fff?text=Risotto',
 '{"spice_level": 1, "prep_time": 45, "popularity": 4.8}'),

('food-3', 'Korean BBQ Tacos', 'Sweet and savory fusion street food with kimchi', 
 ARRAY['pork belly', 'corn tortilla', 'kimchi', 'gochujang sauce', 'sesame seeds'], 
 'Korean-Mexican', 'Lunch',
 'https://via.placeholder.com/300x200/d4203a/fff?text=Korean+Tacos',
 '{"spice_level": 5, "prep_time": 25, "popularity": 4.9}'),

('food-4', 'Mediterranean Bowl', 'Fresh and healthy Mediterranean grain bowl', 
 ARRAY['quinoa', 'chickpeas', 'cucumber', 'tomato', 'feta cheese', 'tahini dressing'], 
 'Mediterranean', 'Lunch',
 'https://via.placeholder.com/300x200/2e8b57/fff?text=Mediterranean',
 '{"spice_level": 2, "prep_time": 20, "popularity": 4.3}'),

('food-5', 'Miso Glazed Salmon', 'Japanese-inspired salmon with miso glaze and vegetables', 
 ARRAY['salmon fillet', 'white miso', 'soy sauce', 'mirin', 'broccoli', 'rice'], 
 'Japanese', 'Dinner',
 'https://via.placeholder.com/300x200/de6b28/fff?text=Miso+Salmon',
 '{"spice_level": 3, "prep_time": 35, "popularity": 4.7}'),

('food-6', 'Mango Avocado Sushi', 'Fresh and vibrant sushi rolls with tropical twist', 
 ARRAY['sushi rice', 'nori', 'avocado', 'mango', 'cucumber', 'cream cheese'], 
 'Japanese', 'Light Meal',
 'https://via.placeholder.com/300x200/f4a460/fff?text=Sushi',
 '{"spice_level": 1, "prep_time": 40, "popularity": 4.6}'),

('food-7', 'Butter Chicken Curry', 'Rich and creamy Indian curry with tender chicken', 
 ARRAY['chicken thigh', 'tomato puree', 'cream', 'butter', 'garam masala', 'ginger garlic'], 
 'Indian', 'Dinner',
 'https://via.placeholder.com/300x200/d2691e/fff?text=Butter+Chicken',
 '{"spice_level": 4, "prep_time": 50, "popularity": 4.9}'),

('food-8', 'Thai Green Curry', 'Aromatic and spicy Thai curry with coconut milk', 
 ARRAY['chicken breast', 'coconut milk', 'green curry paste', 'eggplant', 'basil', 'bamboo shoots'], 
 'Thai', 'Dinner',
 'https://via.placeholder.com/300x200/228b22/fff?text=Thai+Curry',
 '{"spice_level": 5, "prep_time": 35, "popularity": 4.7}'),

('food-9', 'Caprese Flatbread', 'Fresh Italian flatbread with tomato, mozzarella, and basil', 
 ARRAY['flatbread', 'tomato', 'fresh mozzarella', 'basil', 'balsamic glaze'], 
 'Italian', 'Lunch',
 'https://via.placeholder.com/300x200/dc143c/fff?text=Caprese',
 '{"spice_level": 1, "prep_time": 15, "popularity": 4.4}'),

('food-10', 'Chocolate Lava Cake', 'Decadent dessert with warm chocolate center', 
 ARRAY['dark chocolate', 'butter', 'eggs', 'sugar', 'flour', 'vanilla'], 
 'Dessert', 'Dessert',
 'https://via.placeholder.com/300x200/8b4513/fff?text=Lava+Cake',
 '{"spice_level": 0, "prep_time": 25, "popularity": 4.8}'),

('food-11', 'Veggie Burger', 'Plant-based burger with all the fixings', 
 ARRAY['black beans', 'quinoa', 'mushrooms', 'onion', 'garlic', 'whole wheat bun'], 
 'American', 'Lunch',
 'https://via.placeholder.com/300x200/228b22/fff?text=Veggie+Burger',
 '{"spice_level": 2, "prep_time": 30, "popularity": 4.2}'),

('food-12', 'Pineapple Fried Rice', 'Sweet and savory Thai-style fried rice in pineapple shell', 
 ARRAY['jasmine rice', 'pineapple', 'shrimp', 'cashews', 'egg', 'curry powder'], 
 'Thai', 'Dinner',
 'https://via.placeholder.com/300x200/ffa500/fff?text=Fried+Rice',
 '{"spice_level": 3, "prep_time": 30, "popularity": 4.5}');