import os
import google.generativeai as genai
import json

def setup_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    genai.configure(api_key=api_key)

def generate_recipe(preferences, dietary_restrictions, servings, additional_info=""):
    """Generate a recipe based on user preferences"""
    setup_gemini()
    
    restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "None"
    
    prompt = f"""
    Create a recipe with the following specifications:
    - Preferences: {preferences}
    - Dietary Restrictions: {restrictions_text}
    - Servings: {servings}
    - Additional Information: {additional_info}
    
    Please format your response as a JSON object with the following structure:
    {{
        "title": "Recipe Title",
        "description": "Brief description of the dish",
        "prep_time": "Preparation time in minutes",
        "cook_time": "Cooking time in minutes",
        "servings": {servings},
        "ingredients": [
            "Ingredient 1 with quantity",
            "Ingredient 2 with quantity"
        ],
        "instructions": [
            "Step 1",
            "Step 2"
        ],
        "nutrition_info": {{
            "calories": "per serving",
            "protein": "in grams",
            "carbs": "in grams",
            "fat": "in grams"
        }},
        "shopping_list": [
            "Categorized shopping list items"
        ]
    }}
    """
    
    model = genai.GenerativeModel('models/gemini-2.0-pro-exp-02-05')
    response = model.generate_content(prompt)
    
    try:
        response_text = response.text
        json_str = response_text
        
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
            
        recipe_data = json.loads(json_str)
        return recipe_data
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {"error": "Failed to generate recipe. Please try again."}

def generate_recipes_from_ingredients(ingredients, preferences="", dietary_restrictions=None, servings=2):
    """Generate recipe ideas based on available ingredients"""
    setup_gemini()
    
    ingredients_text = ", ".join(ingredients)
    restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "None"
    
    prompt = f"""
    Create three recipe ideas using mainly these ingredients:
    {ingredients_text}
    
    Additional context:
    - Preferences: {preferences}
    - Dietary Restrictions: {restrictions_text}
    - Servings: {servings}
    
    Format your response as a JSON array with 3 recipe objects, each having this structure:
    {{
        "title": "Recipe Title",
        "description": "Brief description",
        "ingredients_required": ["Ingredients from the provided list"],
        "additional_ingredients_needed": ["Any extra ingredients needed"],
        "difficulty": "Easy/Medium/Hard",
        "estimated_time": "Total preparation and cooking time"
    }}
    """
    
    model = genai.GenerativeModel('models/gemini-2.0-pro-exp-02-05')
    response = model.generate_content(prompt)
    
    try:
        response_text = response.text
        json_str = response_text
        
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
            
        recipe_ideas = json.loads(json_str)
        return recipe_ideas
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {"error": "Failed to generate recipe ideas. Please try again."}

if __name__ == "__main__":
    recipe = generate_recipe("spicy Italian", ["vegetarian"], 4, "use fresh herbs")
    print(json.dumps(recipe, indent=2))
    
    ingredients = ["tomatoes", "pasta", "olive oil"]
    recipes = generate_recipes_from_ingredients(ingredients, "savory", ["gluten-free"], 2)
    print(json.dumps(recipes, indent=2))
