# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.tests.test_tryton import ModuleTestCase


class BenchTestCase(ModuleTestCase):
    'Test Bench module'
    module = 'bench'


del ModuleTestCase
