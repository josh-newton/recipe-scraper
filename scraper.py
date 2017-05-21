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

bbcBaseUrl = 'https://www.bbc.co.uk'
baseSearchUrl = 'https://www.bbc.co.uk/food/recipes/search?page='
titleError = 'BBC - Food - Recipe finder : No results'

courseBase = 'courses[0]='
cuisineBase = 'cuisines[0]='
dietsBase = 'diets[0]='

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
	'recipeLink': 'div#article-list h3 a',
	'title': 'h1.content-title__text',
	'image': 'img.recipe-media__image',
	'description': 'p.recipe-description__text',
	'method': 'ol.recipe-method__list li p',
	'ingredients': '.recipe-ingredients__list li',
	'chef': 'div.chef__name .chef__link',
	'prepTime': 'p.recipe-metadata__prep-time',
	'cookTime': 'p.recipe-metadata__cook-time',
	'serves': 'p.recipe-metadata__serving'
}

def saveRecipeDetails(url, cuisine):
	try:
		page = browser.open(url)
		html = page.read()
		soup = BeautifulSoup(html, 'lxml')

		title = soup.select(selectors['title'])[0].text
		print 'Grabbing recipe: ' + title

		try:
			# Strip removes newline and whitespace characters
			description = soup.select(selectors['description'])[0].text.strip()
		except:
			description = ''

		ingredients = soup.select(selectors['ingredients'])
		# Grab whole ingredient text with the amount of ingredient ie 400ml water
		ingredientText = []
		# Isolate just the ingredient name from the ingredient text
		ingredientItem = []
		for ingredient in ingredients:
			ingredientText.append(ingredient.text.strip())
			# Attempt to isolate ingredient name
			if ingredient.select('a'):
				if ingredient.select('a')[0]:
					ingredientItem.append(ingredient.select('a')[0].text)
			else:
				# if not possible just keep ingredient text
				ingredientItem.append(ingredient.text.strip())
		# Remove duplicates
		ingredientItem = list(set(ingredientItem))

		# Grab cooking method
		methodList = soup.select(selectors['method'])
		methodText = []
		for method in methodList:
			methodText.append(method.text.strip())

		try:
			imageTag = soup.select(selectors['image'])
			if imageTag[0].has_attr('src'):
				imageSrc = imageTag[0]['src']
				# imageSrc includes bbc href, we just want to take the image filename
				filename = imageSrc.split('/')[-1]
				cwd = os.getcwd()
				downloadedImgLoc = 'images/' + filename
				# Download image to images directory
	        	urllib.urlretrieve(imageSrc, cwd + '/images/' + filename)
		except:
			downloadedImgLoc = ''

		try:
			chefName = soup.select(selectors['chef'])[0].text.strip()
		except:
			chefName = ''

		try:
			prepTime = soup.select(selectors['prepTime'])[0].text.strip()
		except:
			prepTime = ''

		try:
			cookTime = soup.select(selectors['cookTime'])[0].text.strip()
		except:
			cookTime = ''

		try:
			serves = soup.select(selectors['serves'])[0].text.strip()
		except:
			serves = ''


		ordered = OrderedDict([("title", title), ("description", description), ("cuisine", cuisine), ("image", downloadedImgLoc), ("sourceUrl", url), ("chefName", chefName), ("preparationTime", prepTime), ("cookingTime", cookTime), ("serves", serves), ("ingredientsDesc", ingredientText), ("ingredients", ingredientItem), ("method", methodText)])
		appendToJsonFile(ordered)
		appendToXmlFile(ordered)
	except:
		pass

def appendToJsonFile(dictionary):
	jsonFile.write(json.dumps(dictionary, sort_keys=False, indent=4, separators=(',', ': ')) + ',\n')

def appendToXmlFile(dictionary):
	dictXml = dicttoxml.dicttoxml(dictionary, custom_root='recipe', attr_type=False)
	xmlString = xml.dom.minidom.parseString(dictXml)
	prettyXml = xmlString.toprettyxml()
	# Fix utf-8 encoding error, remove xml verion tag
	prettyXml = prettyXml.encode('utf-8')[23:]
	xmlFile.write(prettyXml)

def stitchUrl(pageNum, categoryBase, catergoryId):
	return baseSearchUrl + pageNum + '&' + categoryBase + catergoryId

# Is there a better way of detecting this. BBC does not throw 404 error. Could check for h3.error has string 'No Results Found'
def pageExists(url):
    page = browser.open(url)
    title = browser.title()
    if title == titleError:
        return False
    else:
        return True

def grabRecipeLinksFromPage(url):
    page = browser.open(url)
    html = page.read()
    soup = BeautifulSoup(html, 'lxml')
    recipeLinks = soup.select(selectors['recipeLink'])
    return recipeLinks

def saveRecipesInCategory(categoryBase, categoryId):
	# Start on first page
	currPage = 1
	# Get url
	url = stitchUrl(str(currPage), categoryBase, categoryId)
	# While the page exists
	while pageExists(url):
		# Get all recipe links from the new page
		newLinks = grabRecipeLinksFromPage(url)
		# add to url list
		for link in newLinks:
			if link.has_attr('href'):
				# Go to the recipe page and grab its details
				saveRecipeDetails(bbcBaseUrl + link['href'], categoryId)

		# Update for next loop
		currPage += 1
		url = stitchUrl(str(currPage), categoryBase, categoryId)

def saveRecipesByCuisine():
	for cuisine in cuisines:
		saveRecipesInCategory(cuisineBase, cuisine)


def main():
	# create images directory/remove images contents at start
	if os.path.exists(os.getcwd() + '/images/'):
		filelist = glob.glob(os.getcwd() + "/images/*")
		for f in filelist:
			os.remove(f)
	else:
	    os.makedirs(os.getcwd() + '/images/')

	jsonFile.write('[\n')
	saveRecipesByCuisine()
	jsonFile.write(']')

	# Loop over all cuisines - cusines[0]=x
		# Go to a cuisine page
		# Get recipe links from page
			# Go to recipe page and grab details
			# Add recipe details to json and xml
	# Loop over all course pages - courses[0]=x
		# Get recipe url, match to an already downloaded recipe, add course to details
		# If no recipe match, go to recipe page and grab details
	# Loop over all diet pages - diets[0]=x
		# Get recipe title, match to an already downloaded recipe, add course to details
		# If no recipe match, go to recipe page and grab details

if __name__ == '__main__':
	main()
