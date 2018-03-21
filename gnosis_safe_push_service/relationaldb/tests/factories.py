# -*- coding: utf-8 -*-
import factory as factory_boy
from factory.fuzzy import FuzzyDateTime
from faker import Factory as FakerFactory
from faker import Faker

from .. import models

fakerFactory = FakerFactory.create()
faker = Faker()
