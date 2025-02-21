import os
import google.generativeai as genai
import json
import streamlit as st  # Add this import if not already in your app.py

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
    model = genai.GenerativeModel('models/gemini-flash-2.0')
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
    model = genai.GenerativeModel('models/gemini-flash-2.0')
    response = model.generate_content(prompt)
    try:
        response_text = response.text
        json_str = response_text
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
        recipe_ideas = json.loads(json_str)
        
        # Initialize session state for selected recipe
        if "selected_recipe" not in st.session_state:
            st.session_state.selected_recipe = None

        # Display the three recipe ideas
        if isinstance(recipe_ideas, list) and len(recipe_ideas) == 3:
            for i, idea in enumerate(recipe_ideas):
                st.subheader(f"Option {i+1}: {idea['title']}")
                st.write(f"**Description**: {idea['description']}")
                st.write(f"**Ingredients Required**: {', '.join(idea['ingredients_required'])}")
                st.write(f"**Additional Ingredients**: {', '.join(idea['additional_ingredients_needed'])}")
                st.write(f"**Difficulty**: {idea['difficulty']}")
                st.write(f"**Estimated Time**: {idea['estimated_time']}")
                
                # Button to generate full recipe
                if st.button(f"Generate Full Recipe for {idea['title']}", key=f"gen_recipe_{i}"):
                    st.session_state.selected_recipe = idea

        # If a recipe is selected, generate and display the full recipe
        if st.session_state.selected_recipe:
            selected = st.session_state.selected_recipe
            full_recipe = generate_recipe(
                preferences=selected["title"],  # Use title as preference
                dietary_restrictions=dietary_restrictions,
                servings=servings,
                additional_info=f"Based on ingredients: {ingredients_text}"
            )
            st.subheader(f"Full Recipe: {full_recipe.get('title', 'Recipe')}")
            st.write(f"**Description**: {full_recipe.get('description', '')}")
            st.write(f"**Prep Time**: {full_recipe.get('prep_time', 'N/A')}")
            st.write(f"**Cook Time**: {full_recipe.get('cook_time', 'N/A')}")
            st.write(f"**Servings**: {full_recipe.get('servings', servings)}")
            st.write("**Ingredients**:")
            for ing in full_recipe.get("ingredients", []):
                st.write(f"- {ing}")
            st.write("**Instructions**:")
            for step in full_recipe.get("instructions", []):
                st.write(f"- {step}")
            st.write("**Nutrition Info**:")
            nutrition = full_recipe.get("nutrition_info", {})
            st.write(f"- Calories: {nutrition.get('calories', 'N/A')}")
            st.write(f"- Protein: {nutrition.get('protein', 'N/A')}")
            st.write(f"- Carbs: {nutrition.get('carbs', 'N/A')}")
            st.write(f"- Fat: {nutrition.get('fat', 'N/A')}")
            st.write(f"**Shopping List**: {', '.join(full_recipe.get('shopping_list', []))}")
            # Optional: Reset button to go back to options
            if st.button("Back to Options"):
                st.session_state.selected_recipe = None
                
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
