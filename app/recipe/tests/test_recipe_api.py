from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main food'):
    """Create and return a sample tag object"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample ingredient object"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipesApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the endpoint"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTests(TestCase):
    """Test authenticate recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='testpass',
        )
        self.client.force_authenticate(self.user)

    def test_retrive_recipes_list(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        user2 = get_user_model().objects.create_user(
            email='otheruser@user.com',
            password='testpass',
        )
        recipe = sample_recipe(user=self.user, title='different')
        sample_recipe(user=user2)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], recipe.title)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creat a new recipe"""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        exists = Recipe.objects.filter(
            title=payload['title'],
            time_minutes=payload['time_minutes'],
            price=payload['price'],
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

        # this test is excessive and just to show other way of doing it
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Dessert')
        tag2 = sample_tag(user=self.user, name='Main food')

        payload = {
            'title': 'Red Curry',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 22,
            'price': 11.00
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredient(self):
        """Test creating a recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name='Salt')
        ingredient2 = sample_ingredient(user=self.user, name='Carrot')

        payload = {
            'title': 'Soup of day',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 15,
            'price': 10.00,
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user, name="Vegan"))
        new_tag = sample_tag(user=self.user, name='Main food')

        url = detail_url(recipe.id)

        payload = {
            'title': 'Butter chicken',
            'tags': [new_tag.id]
        }

        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])

        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Vegtable omlet',
            'time_minutes': 17,
            'price': 12.00,
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()

        for key in payload.keys():
            self.assertEqual(getattr(recipe, key), payload[key])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)
