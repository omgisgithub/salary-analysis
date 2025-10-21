def check_ingredient_match(recipe, ingredients):
    ingredients_set = set(ingredients)
    missing = []
    for ingredient in recipe:
        if ingredient not in ingredients_set:
            missing.append(ingredient)
    percent = 100 * (len(recipe) - len(missing)) / len(recipe)
    return percent, missing