import pandas as pd
import speech_recognition as sr
import sys
from googletrans import Translator

# Initialize the recognizer and translator
recognizer = sr.Recognizer()
translator = Translator()

# Supported language codes for speech recognition
SUPPORTED_LANGUAGES = {
    '1': 'en',   # English
    '2': 'id',   # Indonesian
    '3': 'ja',   # Japanese
    '4': 'ko',   # Korean
    '5': 'zh'    # Chinese
}


def load_recipe_dataset(file_path):
    return pd.read_csv(file_path)


def search_recipes(recipe_df, ingredients, missing_ingredient=None):
    matched_recipes = []
    for index, row in recipe_df.iterrows():
        recipe_ingredients = eval(row['NER'])  # Extracting ingredients from NER row
        if missing_ingredient:
            if missing_ingredient.lower() not in recipe_ingredients:
                continue  # Skip recipes containing the missing ingredient
        if all(ingredient in recipe_ingredients for ingredient in ingredients):
            matched_recipes.append(row['title'])
    return matched_recipes


def listen_for_speech(timeout=300, language="en-US"):
    while True:
        with sr.Microphone() as source:
            print("Listening for speech...")
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.listen(source, timeout=timeout)
        
        try:
            print("Recognizing speech...")
            user_input = recognizer.recognize_google(audio_data, language=language, show_all=True)  
            recognized_text = user_input['alternative'][0]['transcript'].lower()  
            confidence = user_input['alternative'][0]['confidence'] 
            
            # Translate recognized text to English if not already in English
            if language != "en-US":
                translated_text = translator.translate(recognized_text, src=language, dest='en').text
                print("Recognized (Translated to English):", translated_text)
                return translated_text, confidence
            else:
                print("Recognized:", recognized_text)
                return recognized_text, confidence
        except sr.UnknownValueError:
            print("Sorry, I could not understand what you said. Please try again.")
        except sr.RequestError:
            print("Sorry, could not request results from Google Speech Recognition service. Check your internet connection.")
            return "", 0


def get_preferred_language():
    print("Please select your preferred language:")
    print("1. English")
    print("2. Indonesian")
    print("3. Japanese")
    print("4. Korean")
    print("5. Chinese")
    choice = input("Enter the number corresponding to your choice: ")
    return SUPPORTED_LANGUAGES.get(choice, "en-US")

# Translate text to the specified language
def translate_to_language(text, language):
    translated_text = translator.translate(text, dest=language).text
    return translated_text


def show_simplest_recipes(recipe_df, num_recipes=10):
    simplest_recipes = recipe_df.sort_values(by=['ingredients', 'directions']).head(num_recipes)
    return simplest_recipes['title']

def main():
    recipe_df = load_recipe_dataset('C:/kuliah/AI/Project/Recipedataset.csv')
    
    # Get user's preferred language
    preferred_language = get_preferred_language()

    user_input_ingredients = []  # Initialize list to store user's ingredients
    
    while True:
        if not user_input_ingredients:
            print("Please speak the ingredients you have.")
            ingredients_input, _ = listen_for_speech(language=preferred_language)
            if ingredients_input:
                user_input_ingredients = ingredients_input.split()
        
        # Search for recipes based on user input ingredients
        matched_recipes = search_recipes(recipe_df, user_input_ingredients)
        
        # Print matched recipes
        if matched_recipes:
            print("Matched recipes:")
            for index, recipe in enumerate(matched_recipes[:20], start=1):  # Limit to the first 20 recipes
                translated_recipe = translate_to_language(recipe, preferred_language)
                print(f"{index}. {translated_recipe} ({recipe})")  


            print("Please say the exact name of the recipe you want to choose.")

            recipe_choice_text, _ = listen_for_speech(timeout=300, language=preferred_language)  # Use preferred language for recipe choice
            recipe_choice_text = recipe_choice_text.lower()

            chosen_recipe = None
            for recipe_title in matched_recipes:
                if isinstance(recipe_title, str) and recipe_choice_text == recipe_title.lower():
                    chosen_recipe = recipe_title
                    break

            while chosen_recipe is None:
                print("Sorry, the specified recipe was not found. Please choose again.")

                recipe_choice_text, _ = listen_for_speech(timeout=300, language=preferred_language)  # Use preferred language for recipe choice
                recipe_choice_text = recipe_choice_text.lower()

                # Find the chosen recipe
                chosen_recipe = None
                for recipe_title in matched_recipes:
                    if isinstance(recipe_title, str) and recipe_choice_text == recipe_title.lower():
                        chosen_recipe = recipe_title
                        break

            
           
            print(f"You have chosen {chosen_recipe}.")
            chosen_recipe_row = recipe_df[recipe_df['title'].str.lower() == chosen_recipe.lower()]
            ingredients = chosen_recipe_row['ingredients'].iloc[0]
            directions = chosen_recipe_row['directions'].iloc[0]
                
            # Translate ingredients and directions to preferred language
            translated_ingredients = translate_to_language(', '.join(eval(ingredients)), preferred_language)
            translated_directions = translate_to_language('. '.join(eval(directions)), preferred_language)
                
            print("\nIngredients:")
            print("\n".join(["- " + ing.strip() for ing in translated_ingredients.split(",")]))
                
            print("\nDirections:")
            print("\n".join(["- " + dir.strip() for dir in translated_directions.split(",")]))
                
        else:
            print("No recipes found with the given ingredients.")
        
        while True:
            print("Speak 'I don't have [ingredient]' to remove specific ingredients, 'show me simple recipes' to find simplest recipes, or say 'No' to exit.")
            additional_input, _ = listen_for_speech(timeout=300, language=preferred_language)
            if additional_input.lower().startswith("i don't have"):
                removed_ingredient = additional_input.lower().replace("i don't have", "").strip()
                user_input_ingredients = [ingredient for ingredient in user_input_ingredients if ingredient != removed_ingredient]
                if removed_ingredient.lower() in SUPPORTED_LANGUAGES.values():
                    print(f"You removed {removed_ingredient}. Let me find recipes without it.")
                    matched_recipes = search_recipes(recipe_df, user_input_ingredients, removed_ingredient)
                    if matched_recipes:
                        print("Here are the recipes without", removed_ingredient, ":")
                        for index, recipe in enumerate(matched_recipes[:20], start=1):
                            translated_recipe = translate_to_language(recipe, preferred_language)
                            print(f"{index}. {translated_recipe} ({recipe})")
                break
            elif additional_input.lower() == "show me simple recipes":
                simplest_recipes = show_simplest_recipes(recipe_df)
                print("Simplest recipes:")
                for index, recipe in enumerate(simplest_recipes[:10], start=1):
                    translated_recipe = translate_to_language(recipe, preferred_language)
                    print(f"{index}. {translated_recipe} ({recipe})")
                continue  
            elif additional_input.lower() == "no":
                print("Exiting the program.")
                sys.exit()  

if __name__ == "__main__":
    main()