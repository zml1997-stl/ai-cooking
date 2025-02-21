import streamlit as st
import os
from dotenv import load_dotenv
import gemini_utils
import auth
import json
import pandas as pd

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Cooking Assistant",
    page_icon="🍳",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .recipe-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #4CAF50;
    }
    .sidebar .sidebar-content {
        background-color: #f1f3f6;
    }
    h1, h2, h3 {
        color: #2E7D32;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        background-color: #388E3C;
    }
</style>
""", unsafe_allow_html=True)

# Setup authentication
auth.setup_auth()

def display_recipe(recipe_data):
    """Display a recipe in a nice format"""
    if "error" in recipe_data:
        st.error(recipe_data["error"])
        return
    
    st.markdown(f"<h2>{recipe_data['title']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p><i>{recipe_data['description']}</i></p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Details")
        st.markdown(f"**Prep Time:** {recipe_data['prep_time']}")
        st.markdown(f"**Cook Time:** {recipe_data['cook_time']}")
        st.markdown(f"**Servings:** {recipe_data['servings']}")
    
    with col2:
        st.markdown("### Nutrition Information")
        st.markdown(f"**Calories:** {recipe_data['nutrition_info']['calories']}")
        st.markdown(f"**Protein:** {recipe_data['nutrition_info']['protein']}")
        st.markdown(f"**Carbs:** {recipe_data['nutrition_info']['carbs']}")
        st.markdown(f"**Fat:** {recipe_data['nutrition_info']['fat']}")
    
    st.markdown("### Ingredients")
    for ingredient in recipe_data['ingredients']:
        st.markdown(f"- {ingredient}")
    
    st.markdown("### Instructions")
    for i, step in enumerate(recipe_data['instructions'], 1):
        st.markdown(f"{i}. {step}")
    
    st.markdown("### Shopping List")
    for item in recipe_data['shopping_list']:
        st.markdown(f"- {item}")

def display_recipe_ideas(recipe_ideas):
    """Display multiple recipe ideas in cards"""
    if isinstance(recipe_ideas, dict) and "error" in recipe_ideas:
        st.error(recipe_ideas["error"])
        return
    
    for recipe in recipe_ideas:
        with st.expander(f"**{recipe['title']}** - {recipe['difficulty']} ({recipe['estimated_time']})"):
            st.markdown(f"**Description:** {recipe['description']}")
            
            st.markdown("**Ingredients You Already Have:**")
            for ingredient in recipe['ingredients_required']:
                st.markdown(f"- {ingredient}")
            
            st.markdown("**Additional Ingredients Needed:**")
            for ingredient in recipe['additional_ingredients_needed']:
                st.markdown(f"- {ingredient}")
            
            if st.button(f"Generate Full Recipe for {recipe['title']}", key=f"full_recipe_{recipe['title']}"):
                with st.spinner("Generating full recipe..."):
                    preferences = f"Recipe for {recipe['title']}: {recipe['description']}"
                    full_recipe = gemini_utils.generate_recipe(
                        preferences=preferences,
                        dietary_restrictions=st.session_state.get('dietary_restrictions', []),
                        servings=st.session_state.get('servings', 2)
                    )
                    # Save to user history
                    auth.save_recipe(
                        st.session_state['username'],
                        f"Full recipe for {recipe['title']}",
                        full_recipe
                    )
                    # Store the full recipe in session state
                    st.session_state.full_recipe = full_recipe

def main():
    if st.session_state['authentication_status'] is not True:
        auth.login_page()
    else:
        # Sidebar
        st.sidebar.title(f"Welcome, {st.session_state['name']}")
        
        # Navigation
        page = st.sidebar.radio("Navigation", ["Generate New Recipe", "Cook with Ingredients", "Recipe History"])
        
        # Logout button
        auth.logout()
        
        if page == "Generate New Recipe":
            st.title("Generate a New Recipe")
            
            col1, col2 = st.columns(2)
            
            with col1:
                preferences = st.text_area("What would you like to cook?", 
                                          placeholder="E.g., A quick pasta dish, A healthy breakfast, etc.")
                servings = st.number_input("Number of servings", min_value=1, max_value=20, value=2)
                st.session_state['servings'] = servings
            
            with col2:
                dietary_options = [
                    "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", 
                    "Keto", "Paleo", "Low-Carb", "Low-Fat", "Nut-Free"
                ]
                dietary_restrictions = st.multiselect("Dietary Restrictions", options=dietary_options)
                st.session_state['dietary_restrictions'] = dietary_restrictions
                additional_info = st.text_area("Additional Information", 
                                              placeholder="Any allergies, preferred ingredients, cooking tools available, etc.")
            
            if st.button("Generate Recipe"):
                if not preferences:
                    st.warning("Please enter what you'd like to cook!")
                else:
                    with st.spinner("Generating your personalized recipe..."):
                        recipe_data = gemini_utils.generate_recipe(
                            preferences=preferences,
                            dietary_restrictions=dietary_restrictions,
                            servings=servings,
                            additional_info=additional_info
                        )
                        auth.save_recipe(
                            st.session_state['username'],
                            preferences,
                            recipe_data
                        )
                        st.markdown("---")
                        st.markdown("## Your Personalized Recipe")
                        display_recipe(recipe_data)
        
        elif page == "Cook with Ingredients":
            st.title("Cook with Available Ingredients")
            
            # Initialize session state for full recipe if not present
            if 'full_recipe' not in st.session_state:
                st.session_state.full_recipe = None

            # If a full recipe is selected, display it
            if st.session_state.full_recipe:
                st.markdown("---")
                st.markdown("## Your Full Recipe")
                display_recipe(st.session_state.full_recipe)
                if st.button("Back to Recipe Ideas"):
                    st.session_state.full_recipe = None  # Reset to show ideas again
            else:
                # Show input form and recipe ideas
                st.write("Enter the ingredients you have on hand, and we'll suggest recipes!")
                ingredients_input = st.text_area(
                    "List your available ingredients (one per line)",
                    height=150,
                    placeholder="Chicken\nRice\nBroccoli\nOnions\nGarlic\nOlive oil"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    preferences = st.text_input("Any specific preferences?", 
                                              placeholder="Quick dinner, Italian cuisine, etc.")
                    servings = st.number_input("Number of servings", min_value=1, max_value=20, value=2, key="ingredients_servings")
                    st.session_state['servings'] = servings
                
                with col2:
                    dietary_options = [
                        "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", 
                        "Keto", "Paleo", "Low-Carb", "Low-Fat", "Nut-Free"
                    ]
                    dietary_restrictions = st.multiselect("Dietary Restrictions", options=dietary_options, key="ingredients_dietary")
                    st.session_state['dietary_restrictions'] = dietary_restrictions
                
                if st.button("Find Recipe Ideas"):
                    if not ingredients_input.strip():
                        st.warning("Please enter some ingredients!")
                    else:
                        ingredients_list = [ing.strip() for ing in ingredients_input.split('\n') if ing.strip()]
                        with st.spinner("Finding recipe ideas based on your ingredients..."):
                            recipe_ideas = gemini_utils.generate_recipes_from_ingredients(
                                ingredients=ingredients_list,
                                preferences=preferences,
                                dietary_restrictions=dietary_restrictions,
                                servings=servings
                            )
                            st.markdown("---")
                            st.markdown("## Recipe Ideas From Your Ingredients")
                            display_recipe_ideas(recipe_ideas)
        
        elif page == "Recipe History":
            st.title("Your Recipe History")
            user_recipes = auth.get_user_recipes(st.session_state['username'])
            if not user_recipes:
                st.info("You haven't generated any recipes yet. Try generating a new recipe!")
            else:
                for idx, recipe_entry in enumerate(user_recipes):
                    recipe_data = recipe_entry['recipe_data']
                    prompt = recipe_entry['prompt']
                    try:
                        from datetime import datetime
                        created_at = datetime.fromisoformat(recipe_entry['created_at']).strftime("%Y-%m-%d %H:%M")
                    except:
                        created_at = recipe_entry.get('created_at', 'Unknown date')
                    with st.expander(f"{recipe_data['title']} - {created_at}"):
                        st.markdown(f"**Original Request:** {prompt}")
                        display_recipe(recipe_data)

if __name__ == "__main__":
    main()​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
