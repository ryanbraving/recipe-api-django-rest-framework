# Recipe API with Django Rest Framework

## Tools & Technologies
```
DjangoRestFramework
PostgresSQL
Test Driven Development (TDD)
TravisCI
Docker
```

## To run project on local machine:

Clone it:
```
git clone git@github.com:ryanbraving/recipe-api-django-rest-framework.git
```

Run project:
```
docker-compose up
```

The api would be available here:
```
http://localhost:8000
```


## Recipe API

Manager users

```
/api/user/create
/api/user/token
/api/user/me
```

Manager recipes:

```
/api/recipe/tags
/api/recipe/ingredients
/api/recipe/recipes
/api/recipe/recipes/<id>
/api/recipe/recipes/<id>/upload-image
