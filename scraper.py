#!/usr/bin/python
import mechanize
import urllib
import os
from bs4 import BeautifulSoup
import json
from collections import OrderedDict
import dicttoxml
import xml.dom.minidom
import glob

browser = mechanize.Browser()
browser.set_handle_robots(False)

# clear files before opening
open(os.getcwd() + '/recipes.json', 'w').close()
open(os.getcwd() + '/recipes.xml', 'w').close()
jsonFile = open(os.getcwd() + '/recipes.json', 'a')
xmlFile = open(os.getcwd() + '/recipes.xml', 'a')

# create images directory/remove images contents at start
if os.path.exists(os.getcwd() + '/images/'):
	filelist = glob.glob(os.getcwd() + "/images/*")
	for f in filelist:
		os.remove(f)
else:
    os.makedirs(os.getcwd() + '/images/')

baseUrl = 'https://www.bbc.co.uk/food/recipes/search?page='
allRecipes = '&cuisines[0]=african&cuisines[1]=american&cuisines[2]=british&cuisines[3]=caribbean&cuisines[4]=chinese&cuisines[5]=east_european&cuisines[6]=french&cuisines[7]=greek&cuisines[8]=indian&cuisines[9]=irish&cuisines[10]=italian&cuisines[11]=japanese&cuisines[12]=mexican&cuisines[13]=nordic&cuisines[14]=north_african&cuisines[15]=portuguese&cuisines[16]=south_american&cuisines[17]=spanish&cuisines[18]=thai_and_south-east_asian&cuisines[19]=turkish_and_middle_eastern'
titleError = 'BBC - Food - Recipe finder : No results'
testCuisine = '&cuisines[0]=african'

courses = [
	'afternoon_tea',
	'brunch',
	'dessert',
	'drinks',
	'light_meals_and_snacks',
	'main_course',
	'other',
	'side_dishes',
	'starters_and_nibbles'
]

cuisines = [
	'african',
	'american',
	'british',
	'caribbean',
	'chinese',
	'east_european',
	'french',
	'greek',
	'indian',
	'irish',
	'italian',
	'japanese',
	'mexican',
	'nordic',
	'north_african',
	'portuguese',
	'south_american',
	'spanish',
	'thai_and_south-east_asian',
	'turkish_and_middle_eastern'
]

diets = [
	'dairy_free',
	'egg_free',
	'gluten_free'
	'nut_free',
	'pregnancy_friendly',
	'shellfish_free',
	'vegan',
	'vegetarian'
]

selectors = {
	'link': 'div#article-list h3 a',
	'title': 'h1.content-title__text'
	'image': 'img.recipe-media__image',
	'description': 'p.recipe-description__text',
	'method': 'ol.recipe-method__list li p',
	'ingredients': '.recipe-ingredients__list li',
	'chef': 'div.chef__name .chef__link',
	'prepTime': 'p.recipe-metadata__prep-time',
	'cookTime': 'p.recipe-metadata__cook-time',
	'serves': 'p.recipe-metadata__serving'
}

recipeLinkSelector = 'div#article-list h3 a'
recipeTitleSelector = 'h1.content-title__text'
recipeImageSelector = 'img.recipe-media__image'
recipeDescriptionSelector = 'p.recipe-description__text'
recipeMethodSelector = 'ol.recipe-method__list li p'
recipeIngredientsSelector = '.recipe-ingredients__list li'
recipeChefSelector = 'div.chef__name .chef__link'
recipePrepTimeSelector = 'p.recipe-metadata__prep-time'
recipeCookTimeSelector = 'p.recipe-metadata__cook-time'
recipeServesSelector = 'p.recipe-metadata__serving'


def stitchUrl(page):
	return baseUrl + page + allRecipes;
	# return baseUrl + page + testCuisine;

def pageExists(url):
    page = browser.open(url)
    title = browser.title()
    if title == titleError:
        return False
    else:
        return True

def loopOverPages():
    currPage = 1;
    url = stitchUrl(str(currPage))
    while pageExists(url):
        recipeUrls = grabRecipeLinksFromListPage(url)
        for recipe in recipeUrls:
            if recipe.has_attr('href'):
                grabRecipeDetails('https://www.bbc.co.uk' + recipe['href'])

        # Update for next loop
        currPage += 1
        url = stitchUrl(str(currPage))

def grabRecipeLinksFromListPage(url):
    page = browser.open(url)
    html = page.read()
    soup = BeautifulSoup(html, 'lxml')
    recipeLinks = soup.select(recipeLinkSelector)
    return recipeLinks

def grabRecipeDetails(url):
	page = browser.open(url)
	html = page.read()
	soup = BeautifulSoup(html, 'lxml')

	title = soup.select(recipeTitleSelector)[0].text
	print 'Grabbing recipe: ' + title

	try:
		# Strip removes newline and whitespace characters
		description = soup.select(recipeDescriptionSelector)[0].text.strip()
	except:
		description = ''

	try:
		ingredients = soup.select(recipeIngredientsSelector)
		ingredientsDescription = []
		ingredientsText = []
		for ingredient in ingredients:
			ingredientsDescription.append(ingredient.text.strip())
			if ingredient.select('a')[0]:
				if ingredient.select('a')[0]:
					ingredientsText.append(ingredient.select('a')[0].text)
			else:
				ingredientsText.append(ingredient.text)
		# Remove duplicates
		ingredientsText = list(set(ingredientsText))
	except:
		ingredientsText = []
		ingredientsDescription = []

	try:
		methodList = soup.select(recipeMethodSelector)
		methodText = []
		for method in methodList:
			methodText.append(method.text)
	except:
		methodText = []

	try:
		imageTag = soup.select(recipeImageSelector)
		if imageTag[0].has_attr('src'):
			imageSrc = imageTag[0]['src']
			filename = imageSrc.split('/')[-1]
			cwd = os.getcwd()
			imgFilename = 'images/' + filename
        	urllib.urlretrieve(imageSrc, cwd + '/images/' + filename)
	except:
		imgFilename = ''

	try:
		chefName = soup.select(recipeChefSelector)[0].text
	except:
		chefName = ''

	try:
		prepTime = soup.select(recipePrepTimeSelector)[0].text
	except:
		prepTime = ''

	try:
		cookTime = soup.select(recipeCookTimeSelector)[0].text
	except:
		cookTime = ''

	try:
		serves = soup.select(recipeServesSelector)[0].text
	except:
		serves = ''

	ordered = OrderedDict([("title", title), ("description", description), ("image", imgFilename), ("sourceUrl", url), ("chefName", chefName), ("preparationTime", prepTime), ("cookingTime", cookTime), ("serves", serves), ("ingredientsDesc", ingredientsDescription), ("ingredients", ingredientsText), ("method", methodText)])
	jsonFile.write(json.dumps(ordered, sort_keys=False, indent=4, separators=(',', ': ')) + ',\n')
	# dictXml = dicttoxml.dicttoxml(ordered, custom_root='recipe')
	# xmlString = xml.dom.minidom.parseString(dictXml)
	# prettyXml = xmlString.toprettyxml()
	# print prettyXml
	# xmlFile.write(a)
	print ''

def main():
	jsonFile.write('[\n')
	loopOverPages()
	jsonFile.write(']')

if __name__ == '__main__':
	main()
