import factory
from .. import models
from django.contrib.gis.geos import Point


def gen_coords():
    """Uses Faker to create geo point using GPS land locations"""
    faker = factory.faker.faker.Faker()
    coords = faker.location_on_land(coords_only=True)
    print(coords)

    return Point(x=float(coords[1]), y=float(coords[0]), srid=4326)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.CustomUser
        django_get_or_create = ("email",)

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    home_location = gen_coords()
