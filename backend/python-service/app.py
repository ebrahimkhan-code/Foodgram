"""
Foodgram Member 1 Recommender - HTTP Service
This service wraps the Python recommender and exposes HTTP endpoints
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the member1 recommender path
RECOMMENDER_PATH = os.path.join(os.path.dirname(__file__), '..', 'member1-recommender')
if RECOMMENDER_PATH not in sys.path:
    sys.path.insert(0, RECOMMENDER_PATH)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global objects
food_catalog = None
dna_generator = None
dna_updater = None
recommend_foods_func = None
score_food_func = None
build_features_func = None

# ============================================
# INITIALIZATION - Using actual functions
# ============================================

def initialize_recommender():
    """Load the recommender components"""
    global food_catalog, recommend_foods_func, score_food_func, build_features_func
    global dna_generator, dna_updater
    
    try:
        logger.info("🚀 Initializing Foodgram Recommender Service...")
        logger.info(f"📁 Recommender path: {RECOMMENDER_PATH}")
        
        # Import the actual functions from pipeline
        try:
            from recommendation.pipeline import recommend_foods, score_food, build_recommendation_features
            recommend_foods_func = recommend_foods
            score_food_func = score_food
            build_features_func = build_recommendation_features
            logger.info("✅ Imported recommend_foods, score_food, build_recommendation_features")
        except ImportError as e:
            logger.warning(f"⚠️ Could not import from pipeline: {e}")
            # Try alternative import
            try:
                import recommendation.pipeline as pipeline
                if hasattr(pipeline, 'recommend_foods'):
                    recommend_foods_func = pipeline.recommend_foods
                if hasattr(pipeline, 'score_food'):
                    score_food_func = pipeline.score_food
                if hasattr(pipeline, 'build_recommendation_features'):
                    build_features_func = pipeline.build_recommendation_features
                logger.info("✅ Imported functions from pipeline module")
            except Exception as e2:
                logger.warning(f"⚠️ Alternative import failed: {e2}")
        
        # Load food catalog
        catalog_path = os.path.join(
            RECOMMENDER_PATH,
            'data/menu_dataset_enriched_claude_FINAL.csv'
        )
        
        if os.path.exists(catalog_path):
            food_catalog = pd.read_csv(catalog_path)
            logger.info(f"✅ Loaded {len(food_catalog)} food items from: {catalog_path}")
        else:
            # Try alternative paths
            alt_paths = [
                os.path.join(RECOMMENDER_PATH, 'data/menu_dataset.csv'),
                os.path.join(RECOMMENDER_PATH, 'data/foods.csv'),
                os.path.join(RECOMMENDER_PATH, 'data/synthetic/foods.csv')
            ]
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    food_catalog = pd.read_csv(alt_path)
                    logger.info(f"✅ Loaded {len(food_catalog)} food items from: {alt_path}")
                    break
            
            if food_catalog is None:
                # Create minimal catalog from available data
                food_catalog = create_minimal_catalog()
                logger.warning(f"⚠️ Created minimal catalog with {len(food_catalog)} items")
        
        # Initialize Taste DNA components
        try:
            from taste_dna.generator import TasteDNAGenerator
            dna_generator = TasteDNAGenerator()
            logger.info("✅ TasteDNAGenerator initialized")
        except ImportError:
            try:
                from taste_dna.generator import Generator
                dna_generator = Generator()
                logger.info("✅ Generator imported as TasteDNAGenerator")
            except ImportError:
                dna_generator = None
                logger.warning("⚠️ DNA Generator not available")
        
        try:
            from taste_dna.updater import TasteDNAUpdater
            dna_updater = TasteDNAUpdater()
            logger.info("✅ TasteDNAUpdater initialized")
        except ImportError:
            try:
                from taste_dna.updater import Updater
                dna_updater = Updater()
                logger.info("✅ Updater imported as TasteDNAUpdater")
            except ImportError:
                dna_updater = None
                logger.warning("⚠️ DNA Updater not available")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_minimal_catalog():
    """Create a minimal food catalog from available data"""
    # Try to load from synthetic data
    try:
        foods_path = os.path.join(RECOMMENDER_PATH, 'data/synthetic/foods.csv')
        if os.path.exists(foods_path):
            return pd.read_csv(foods_path)
    except:
        pass
    
    # Create minimal catalog with sample foods
    data = {
        'food_id': ['food-1', 'food-2', 'food-3', 'food-4', 'food-5'],
        'name': ['Spicy Chicken Pasta', 'Truffle Risotto', 'Korean BBQ Tacos', 'Mediterranean Bowl', 'Miso Salmon'],
        'cuisine': ['Italian-Asian', 'Italian', 'Korean-Mexican', 'Mediterranean', 'Japanese'],
        'protein': ['chicken', 'vegetarian', 'pork', 'vegetarian', 'fish'],
        'flavor': ['spicy', 'savory', 'sweet', 'fresh', 'umami'],
        'spice_level': ['medium', 'mild', 'hot', 'mild', 'medium'],
        'meal_type': ['dinner', 'dinner', 'lunch', 'lunch', 'dinner'],
        'price': [16.99, 18.99, 12.99, 13.99, 22.99],
        'description': [
            'Bold fusion of Italian and Asian flavors',
            'Creamy and earthy Italian classic',
            'Sweet and savory fusion street food',
            'Fresh and healthy grain bowl',
            'Japanese-inspired salmon dish'
        ]
    }
    return pd.DataFrame(data)

# ============================================
# TASTE DNA FUNCTIONS
# ============================================

def build_simple_taste_dna(answers):
    """Build Taste DNA from answers"""
    dna = {
        'cuisine': {},
        'protein': {},
        'flavor': {},
        'spice_level': {},
        'base': {},
        'meal_type': {},
        'preferences': {
            'spicy': 0.5,
            'savory': 0.5,
            'sweet': 0.5,
            'comfort': 0.5,
            'adventurous': 0.5,
            'healthy': 0.5
        }
    }
    
    for answer in answers:
        attr = answer.get('attribute', '').lower()
        value = answer.get('value', '').lower()
        preference = float(answer.get('preference', 1.0))
        
        if attr in dna:
            if isinstance(dna[attr], dict):
                dna[attr][value] = dna[attr].get(value, 0) + (0.2 * preference)
                # Normalize
                total = sum(dna[attr].values())
                if total > 0:
                    for key in dna[attr]:
                        dna[attr][key] = dna[attr][key] / total
            elif attr in dna['preferences']:
                dna['preferences'][attr] = min(1.0, dna['preferences'][attr] + (0.15 * preference))
    
    return dna

# ============================================
# RECOMMENDATION FUNCTIONS
# ============================================

def _safe_float(value, default=0.0):
    """Convert a value to float, tolerating NaN / None / bad strings."""
    try:
        result = float(value)
        # pandas NaN != NaN
        if result != result:
            return default
        return result
    except (TypeError, ValueError):
        return default


def format_food_record(food, score, confidence=None, reason=None):
    """Flatten a raw food record + model score into a frontend-renderable dict."""
    if not isinstance(food, dict):
        try:
            food = dict(food)
        except Exception:
            food = {}

    score = _safe_float(score, 0.0)

    if confidence is None:
        confidence = 'high' if score >= 0.66 else ('medium' if score >= 0.4 else 'low')

    if reason is None:
        reason = 'Recommended based on your taste profile'

    return {
        'food_id': food.get('food_id') or food.get('id') or food.get('name'),
        'name': food.get('name', 'Unknown'),
        'description': food.get('description', ''),
        'cuisine': food.get('cuisine', 'Various'),
        'protein': food.get('protein', ''),
        'flavor': food.get('flavor', ''),
        'spice_level': food.get('spice_level', ''),
        'meal_type': food.get('meal_type', ''),
        'category': food.get('category', ''),
        'restaurant': food.get('restaurant', ''),
        'price': _safe_float(food.get('price'), 0.0),
        'currency': food.get('currency', 'PKR'),
        'rating': _safe_float(food.get('rating'), 0.0),
        'image_url': food.get('image_url', ''),
        'score': round(score, 4),
        'confidence': confidence,
        'reason': reason,
    }


def get_recommendations_from_catalog(taste_dna, limit=10, history=None):
    """Get recommendations using the actual recommender functions"""
    global food_catalog, recommend_foods_func

    if food_catalog is None or len(food_catalog) == 0:
        return []

    # The member1 feature builder expects `history` to be either None or a
    # dict of aggregate interaction counts. A list (what the Node layer sends
    # today) would raise AttributeError inside build_recommendation_features,
    # so anything that isn't a dict is treated as "no history".
    history_arg = history if isinstance(history, dict) else None

    try:
        if recommend_foods_func is not None:
            # Use the actual trained member1 model.
            logger.info("📊 Using member1 recommend_foods (logistic_regression model)")

            # recommend_foods expects a List[Dict], NOT a pandas DataFrame,
            # and the keyword is `top_k` (not `limit`).
            records = food_catalog.to_dict('records')

            result = recommend_foods_func(
                foods=records,
                taste_dna=taste_dna,
                history=history_arg,
                top_k=limit,
            )

            # recommend_foods returns [{"food": {...}, "score": prob}, ...]
            formatted = []
            for item in (result or []):
                if isinstance(item, dict) and 'food' in item:
                    formatted.append(
                        format_food_record(item.get('food', {}), item.get('score', 0.0))
                    )
                elif isinstance(item, dict):
                    # Already-flat dict (defensive).
                    formatted.append(
                        format_food_record(item, item.get('score', 0.0))
                    )
            if formatted:
                return formatted
            logger.warning("⚠️ member1 returned no recommendations; using fallback")
    except Exception as e:
        logger.warning(f"⚠️ recommend_foods failed: {e}")
        import traceback
        traceback.print_exc()

    # Fallback: Simple taste-based scoring (only if the model path fails).
    return simple_recommend(taste_dna, limit)

def simple_recommend(taste_dna, limit=10):
    """Simple fallback recommender (used only if the trained model path fails)."""
    global food_catalog

    if food_catalog is None or len(food_catalog) == 0:
        return []

    # NOTE: we intentionally do NOT call score_food here. score_food expects a
    # pre-built list of exactly 15 numeric features, not a (food, taste_dna)
    # pair, so calling it that way always threw and forced random output.
    try:
        taste_dna = taste_dna or {}
        taste_attrs = ['cuisine', 'protein', 'flavor', 'spice_level', 'meal_type']
        recommendations = []

        for _, row in food_catalog.iterrows():
            row_dict = row.to_dict()
            score = 0.5
            for attr in taste_attrs:
                prefs = taste_dna.get(attr) if isinstance(taste_dna, dict) else None
                if isinstance(prefs, dict) and attr in row_dict:
                    food_val = str(row_dict.get(attr, '')).lower()
                    if food_val in prefs:
                        score += 0.1 * float(prefs[food_val])
            recommendations.append(
                format_food_record(
                    row_dict,
                    min(0.99, score),
                    reason='Recommended based on your taste preferences',
                )
            )

        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]

    except Exception as e:
        logger.error(f"❌ Simple recommend failed: {e}")
        return []

# ============================================
# FLASK ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'food_count': len(food_catalog) if food_catalog is not None else 0,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/taste-dna/generate', methods=['POST'])
def generate_taste_dna():
    """Generate Taste DNA from answers"""
    try:
        data = request.get_json()
        answers = data.get('answers', [])
        
        logger.info(f"🎮 Generating Taste DNA from {len(answers)} answers")
        
        if dna_generator:
            try:
                taste_dna = dna_generator.generate_from_answers(answers)
                return jsonify({
                    'success': True,
                    'taste_dna': taste_dna.to_dict() if hasattr(taste_dna, 'to_dict') else taste_dna,
                    'answers_processed': len(answers)
                })
            except Exception as e:
                logger.warning(f"⚠️ DNA Generator failed: {e}")
        
        # Fallback
        taste_dna = build_simple_taste_dna(answers)
        
        return jsonify({
            'success': True,
            'taste_dna': taste_dna,
            'answers_processed': len(answers)
        })
        
    except Exception as e:
        logger.error(f"❌ Taste DNA generation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/taste-dna/update', methods=['POST'])
def update_taste_dna():
    """Update Taste DNA based on interaction"""
    try:
        data = request.get_json()
        current_dna = data.get('taste_dna', {})
        interaction = data.get('interaction', {})
        
        logger.info(f"🔄 Updating Taste DNA with {interaction.get('type')}")
        
        if dna_updater:
            try:
                updated_dna = dna_updater.update(current_dna, interaction)
                return jsonify({
                    'success': True,
                    'taste_dna': updated_dna
                })
            except Exception as e:
                logger.warning(f"⚠️ DNA Updater failed: {e}")
        
        # Simple update fallback
        updated_dna = simple_update_dna(current_dna, interaction)
        
        return jsonify({
            'success': True,
            'taste_dna': updated_dna
        })
        
    except Exception as e:
        logger.error(f"❌ Taste DNA update failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def simple_update_dna(dna, interaction):
    """Simple DNA update fallback"""
    import copy
    updated = copy.deepcopy(dna)
    
    interaction_type = interaction.get('type', '')
    food_attrs = interaction.get('food_attributes', {})
    
    # Update values based on interaction
    delta = 0
    if interaction_type == 'like':
        delta = 0.10
    elif interaction_type == 'save':
        delta = 0.15
    elif interaction_type == 'dislike':
        delta = -0.15
    elif interaction_type == 'skip':
        delta = -0.05
    
    if delta != 0:
        for attr, value in food_attrs.items():
            if attr in updated and value:
                if isinstance(updated[attr], dict):
                    updated[attr][value] = min(1.0, max(-1.0, updated[attr].get(value, 0) + delta))
    
    return updated

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get personalized food recommendations"""
    try:
        data = request.get_json()
        taste_dna = data.get('taste_dna', {})
        history = data.get('history', [])
        context = data.get('context', {})
        limit = data.get('limit', 10)
        
        logger.info(f"🎯 Getting recommendations")
        
        recommendations = get_recommendations_from_catalog(taste_dna, limit, history)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"❌ Recommendation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recommendations/explore', methods=['POST'])
def get_exploration_recommendations():
    """Get exploration recommendations"""
    try:
        data = request.get_json()
        taste_dna = data.get('taste_dna', {})
        history = data.get('history', [])
        limit = data.get('limit', 8)
        
        logger.info(f"🔍 Getting exploration recommendations")
        
        recommendations = get_recommendations_from_catalog(taste_dna, limit, history)
        
        # Mark as exploration
        for rec in recommendations:
            rec['type'] = 'exploration'
            if 'reason' not in rec:
                rec['reason'] = 'Try something new! 🚀'
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"❌ Exploration recommendation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/game/questions', methods=['GET'])
def get_game_questions():
    """Get Rapid Fire game questions"""
    try:
        questions = generate_questions()
        return jsonify({
            'success': True,
            'questions': questions,
            'total': len(questions)
        })
    except Exception as e:
        logger.error(f"❌ Failed to generate questions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_questions():
    """Generate Rapid Fire questions"""
    return [
        {
            'id': 'q1',
            'type': 'cuisine',
            'text': 'Which cuisine do you prefer?',
            'options': [
                {'id': 'cuisine_italian', 'text': 'Italian 🍝', 'value': 'italian'},
                {'id': 'cuisine_mexican', 'text': 'Mexican 🌮', 'value': 'mexican'},
                {'id': 'cuisine_chinese', 'text': 'Chinese 🥡', 'value': 'chinese'},
                {'id': 'cuisine_indian', 'text': 'Indian 🍛', 'value': 'indian'}
            ]
        },
        {
            'id': 'q2',
            'type': 'protein',
            'text': 'What protein do you prefer?',
            'options': [
                {'id': 'protein_chicken', 'text': 'Chicken 🐔', 'value': 'chicken'},
                {'id': 'protein_beef', 'text': 'Beef 🥩', 'value': 'beef'},
                {'id': 'protein_fish', 'text': 'Fish 🐟', 'value': 'fish'},
                {'id': 'protein_vegetarian', 'text': 'Vegetarian 🌱', 'value': 'vegetarian'}
            ]
        },
        {
            'id': 'q3',
            'type': 'flavor',
            'text': 'Which flavor profile do you enjoy?',
            'options': [
                {'id': 'flavor_savory', 'text': 'Savory 🧂', 'value': 'savory'},
                {'id': 'flavor_spicy', 'text': 'Spicy 🌶️', 'value': 'spicy'},
                {'id': 'flavor_sweet', 'text': 'Sweet 🍯', 'value': 'sweet'},
                {'id': 'flavor_smoky', 'text': 'Smoky 🔥', 'value': 'smoky'}
            ]
        },
        {
            'id': 'q4',
            'type': 'spice_level',
            'text': 'How spicy do you like your food?',
            'options': [
                {'id': 'spice_mild', 'text': 'Mild 🌶️', 'value': 'mild'},
                {'id': 'spice_medium', 'text': 'Medium 🌶️🌶️', 'value': 'medium'},
                {'id': 'spice_hot', 'text': 'Hot 🌶️🌶️🌶️', 'value': 'hot'},
                {'id': 'spice_extra_hot', 'text': 'Extra Hot 🔥🔥🔥', 'value': 'extra_hot'}
            ]
        },
        {
            'id': 'q5',
            'type': 'meal_type',
            'text': 'What meal are you looking for?',
            'options': [
                {'id': 'meal_breakfast', 'text': 'Breakfast 🍳', 'value': 'breakfast'},
                {'id': 'meal_lunch', 'text': 'Lunch 🥗', 'value': 'lunch'},
                {'id': 'meal_dinner', 'text': 'Dinner 🍽️', 'value': 'dinner'},
                {'id': 'meal_dessert', 'text': 'Dessert 🍰', 'value': 'dessert'}
            ]
        },
        {
            'id': 'q6',
            'type': 'mood',
            'text': 'What are you in the mood for?',
            'options': [
                {'id': 'mood_comfort', 'text': 'Comfort food 🥘', 'value': 'comfort'},
                {'id': 'mood_adventurous', 'text': 'Adventurous 🧭', 'value': 'adventurous'},
                {'id': 'mood_healthy', 'text': 'Healthy 🥬', 'value': 'healthy'},
                {'id': 'mood_quick', 'text': 'Quick bite ⏱️', 'value': 'quick'}
            ]
        }
    ]

# ============================================
# START SERVER
# ============================================

if __name__ == '__main__':
    # Bind to a DEDICATED port for the recommender service. It must NOT be 5000,
    # because the Node/Express backend already runs there. The Node layer looks
    # for this service at MEMBER1_API_URL (default http://localhost:8000).
    port = int(os.environ.get('MEMBER1_PORT', os.environ.get('FLASK_PORT', 8000)))

    logger.info("=" * 40)
    logger.info("Foodgram Recommender Service")
    logger.info("=" * 40)
    logger.info(f"Python Service Path : {os.path.dirname(__file__)}")
    logger.info(f"Recommender Path    : {RECOMMENDER_PATH}")

    # Initialize
    init_success = initialize_recommender()

    if init_success:
        logger.info("✅ Service initialized successfully!")
    else:
        logger.warning("⚠️ Service started with limited functionality (fallback mode)")

    logger.info(f"🚀 Starting server on http://localhost:{port}")
    # use_reloader=False so the recommender/model is only loaded once.
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)