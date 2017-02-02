# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from .bench import Bench


def register():
    Pool.register(
	Bench
        module='bench', type_='model')
