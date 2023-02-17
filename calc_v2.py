# imports
import re
import pprint
import sympy
from collections import namedtuple


# base classes
class recipe():
    def __init__(self, inputs, outputs, rate, machine, name=None):
        self.inputs = inputs
        self.outputs = outputs
        self.rate = rate
        self.machine = machine
        assert machine in machine_order, machine

        # set this recipe's primary_output. Check that only one such output exists
        self.primary_output = None
        for output in self.outputs:
            if output.is_primary:
                if self.primary_output is None:
                    self.primary_output = output
                else:
                    raise AttributeError(f'multiple primary outputs, {[str(x) for x in self.outputs]}')

        assert name is not None or self.primary_output is not None
        self.name = name or self.primary_output.name

    def copy(self):
        return recipe([x.copy() for x in self.inputs], [x.copy() for x in self.outputs], self.rate, self.machine, self.name)

    def __str__(self):
        return f'inputs: {[str(x) for x in self.inputs]}, outputs: {[str(x) for x in self.outputs]}, rate: {self.rate}, machine: {self.machine}, primary_output: {self.primary_output}'


all_ingredients = set()
class ingredient():
    def __init__(self, name, number, is_primary=True):
        self.name = name
        self.number = number
        self.is_primary = is_primary  # only relevant for recipe outputs

        # update global list of all ingredient names
        all_ingredients.add(self.name)

    def copy(self):
        return ingredient(self.name, self.number, self.is_primary)

    def __str__(self):
        return f'Ingredient: {self.number} x {self.name}, is_primary: {self.is_primary}'


class production_line():
    def __init__(self, ing):
        self.ing = ing.copy()

        if not self.ing.name in raw_inputs:
            self.recipe = recipes[self.ing.name]
            self.num_machines = self.ing.number / self.recipe.rate
            self.sort_key = (machine_order.index(self.recipe.machine), self.ing.name)

            scale_factor = self.ing.number
            if self.recipe.primary_output is not None:
                scale_factor /= self.recipe.primary_output.number

            self.inputs = [ing.copy() for ing in self.recipe.inputs]
            for ing in self.inputs:
                ing.number *= scale_factor

            self.excess_outputs = [ing.copy() for ing in self.recipe.outputs if not ing.is_primary]
            for ing in self.excess_outputs:
                ing.number *= scale_factor

        else:
            self.sort_key = (-1, self.ing.name)

    def __str__(self):
        if self.ing.name in raw_inputs:
            s = 'Raw Input: '
        else:
            s = 'Line: '

        s += f'{self.ing.number:.1f} x {self.ing.name}'
        
        if not self.ing.name in raw_inputs:
            s += f' ({self.num_machines:.2f} x {self.recipe.machine})'
            for ing in self.excess_outputs:
                s += f'\n    Recycle: {ing.number:.2f} x {ing.name}'
            for ing in self.inputs:
                s += f'\n    Ingredient: {ing.number:.2f} x {ing.name}'
        
        return s


machine_order = ['smelter', 'foundry', 'refinery', 'fuel generator', 'constructor', 'assembler', 'manufacturer', 'packager']


# recipes
# comment out alternative recipies to remove pathways
recipes = [
    recipe(inputs =  [ingredient(name = 'iron ore',                number = 1)],
           outputs = [ingredient(name = 'iron ingot',              number = 1)],
           rate = 30, machine = 'smelter'),

    # recipe(inputs =  [ingredient(name = 'copper ore',              number = 1)],
    #        outputs = [ingredient(name = 'copper ingot',            number = 1)],
    #        rate = 30, machine = 'smelter'),
    recipe(inputs =  [ingredient(name = 'copper ore',              number = 6),
                      ingredient(name = 'water',                   number = 4)],
           outputs = [ingredient(name = 'copper ingot',            number = 15)],
           rate = 37.5, machine = 'refinery'),

    recipe(inputs =  [ingredient(name = 'caterium ore',            number = 3)],
           outputs = [ingredient(name = 'caterium ingot',          number = 1)],
           rate = 15, machine = 'smelter'),

    recipe(inputs =  [ingredient(name = 'iron ore',                number = 3),
                      ingredient(name = 'coal',                    number = 3)],
           outputs = [ingredient(name = 'steel ingot',             number = 3)],
           rate = 45, machine = 'foundry'),
    # recipe(inputs =  [ingredient(name = 'iron ore',                number = 6),
    #                   ingredient(name = 'compacted coal',          number = 3)],
    #        outputs = [ingredient(name = 'steel ingot',             number = 10)],
    #        rate = 37.5, machine = 'foundry'),

    # recipe(inputs =  [ingredient(name = 'steel ingot',             number = 3),
    #                   ingredient(name = 'plastic',                 number = 2)],
    #        outputs = [ingredient(name = 'iron plate',              number = 18)],
    #        rate = 45, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'iron ingot',              number = 3)],
           outputs = [ingredient(name = 'iron plate',              number = 2)],
           rate = 20, machine = 'constructor'),

    recipe(inputs =  [ingredient(name = 'iron ingot',              number = 1)],
           outputs = [ingredient(name = 'iron rod',                number = 1)],
           rate = 15, machine = 'constructor'),

    recipe(inputs =  [ingredient(name = 'copper ingot',            number = 1)],
           outputs = [ingredient(name = 'wire',                    number = 2)],
           rate = 30, machine = 'constructor'),
    # recipe(inputs =  [ingredient(name = 'iron ingot',              number = 5)],
    #        outputs = [ingredient(name = 'wire',                    number = 9)],
    #        rate = 22.5, machine = 'constructor'),

    recipe(inputs =  [ingredient(name = 'wire',                    number = 2)],
           outputs = [ingredient(name = 'cable',                   number = 1)],
           rate = 30, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'limestone',               number = 3)],
           outputs = [ingredient(name = 'concrete',                number = 1)],
           rate = 15, machine = 'constructor'),

    # recipe(inputs =  [ingredient(name = 'iron rod',                number = 1)],
    #        outputs = [ingredient(name = 'screw',                   number = 4)],
    #        rate = 40, machine = 'constructor'),
    # recipe(inputs =  [ingredient(name = 'iron ingot',              number = 5)],
    #        outputs = [ingredient(name = 'screw',                   number = 20)],
    #        rate = 50, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'steel beam',              number = 1)],
           outputs = [ingredient(name = 'screw',                   number = 52)],
           rate = 260, machine = 'constructor'),

    # recipe(inputs =  [ingredient(name = 'iron plate',              number = 6),
    #                   ingredient(name = 'screw',                   number = 12)],
    #        outputs = [ingredient(name = 'reinforced iron plate',   number = 1)],
    #        rate = 5, machine = 'assembler'),
    # recipe(inputs =  [ingredient(name = 'iron plate',              number = 3),
    #                   ingredient(name = 'rubber',                  number = 1)],
    #        outputs = [ingredient(name = 'reinforced iron plate',   number = 1)],
    #        rate = 3.75, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'iron plate',              number = 10),
                      ingredient(name = 'wire',                    number = 20)],
           outputs = [ingredient(name = 'reinforced iron plate',   number = 3)],
           rate = 5.625, machine = 'assembler'),

    recipe(inputs =  [ingredient(name = 'copper ingot',            number = 2)],
           outputs = [ingredient(name = 'copper sheet',            number = 1)],
           rate = 10, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'iron rod',                number = 5),
                      ingredient(name = 'screw',                   number = 25)],
           outputs = [ingredient(name = 'rotor',                   number = 1)],
           rate = 4, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'reinforced iron plate',   number = 3),
                      ingredient(name = 'iron rod',                number = 12)],
           outputs = [ingredient(name = 'modular frame',           number = 2)],
           rate = 2, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'reinforced iron plate',   number = 1),
                      ingredient(name = 'rotor',                   number = 1)],
           outputs = [ingredient(name = 'smart plating',           number = 1)],
           rate = 2, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'quartz',                  number = 5)],
           outputs = [ingredient(name = 'quartz crystal',          number = 3)],
           rate = 22.5, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'quartz',                  number = 3)],
           outputs = [ingredient(name = 'silica',                  number = 5)],
           rate = 37.5, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'coal',                    number = 1),
                      ingredient(name = 'sulfur',                  number = 1)],
           outputs = [ingredient(name = 'black powder',            number = 2)],
           rate = 30, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'steel ingot',             number = 4)],
           outputs = [ingredient(name = 'steel beam',              number = 1)],
           rate = 15, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'steel ingot',             number = 3)],
           outputs = [ingredient(name = 'steel pipe',              number = 2)],
           rate = 20, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'modular frame',           number = 1),
                      ingredient(name = 'steel beam',              number = 12)],
           outputs = [ingredient(name = 'versatile framework',     number = 2)],
           rate = 5, machine = 'assembler'),

    # recipe(inputs =  [ingredient(name = 'steel beam',              number = 4),
    #                   ingredient(name = 'concrete',                number = 5)],
    #        outputs = [ingredient(name = 'encased industrial beam', number = 1)],
    #        rate = 6, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'steel pipe',              number = 7),
                      ingredient(name = 'concrete',                number = 5)],
           outputs = [ingredient(name = 'encased industrial beam', number = 1)],
           rate = 4, machine = 'assembler'),

    recipe(inputs =  [ingredient(name = 'steel pipe',              number = 3),
                      ingredient(name = 'wire',                    number = 8)],
           outputs = [ingredient(name = 'stator',                  number = 1)],
           rate = 5, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'rotor',                   number = 2),
                      ingredient(name = 'stator',                  number = 2)],
           outputs = [ingredient(name = 'motor',                   number = 1)],
           rate = 5, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'stator',                  number = 1),
                      ingredient(name = 'cable',                   number = 20)],
           outputs = [ingredient(name = 'automated wiring',        number = 1)],
           rate = 2.5, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'modular frame',           number = 5),
                      ingredient(name = 'steel pipe',              number = 15),
                      ingredient(name = 'encased industrial beam', number = 5),
                      ingredient(name = 'screw',                   number = 100)],
           outputs = [ingredient(name = 'heavy modular frame',     number = 1)],
           rate = 2, machine = 'manufacturer'),
    recipe(inputs =  [ingredient(name = 'coal',                    number = 5),
                      ingredient(name = 'sulfur',                  number = 5)],
           outputs = [ingredient(name = 'compacted coal',          number = 5)],
           rate = 25, machine = 'assembler'),

    recipe(inputs =  [ingredient(name = 'oil',                     number = 3)],
           outputs = [ingredient(name = 'plastic',                 number = 2),
                      ingredient(name = 'heavy oil residue',       number = 1, is_primary = False)],
           rate = 20, machine = 'refinery'),
    # recipe(inputs =  [ingredient(name = 'polymer resin',           number = 6),
    #                   ingredient(name = 'water',                   number = 2)],
    #        outputs = [ingredient(name = 'plastic',                 number = 2)],
    #        rate = 20, machine = 'refinery'),

    recipe(inputs =  [ingredient(name = 'oil',                     number = 3)],
           outputs = [ingredient(name = 'rubber',                  number = 2),
                      ingredient(name = 'heavy oil residue',       number = 2, is_primary = False)],
           rate = 20, machine = 'refinery'),
    # recipe(inputs =  [ingredient(name = 'polymer resin',           number = 4),
    #                   ingredient(name = 'water',                   number = 4)],
    #        outputs = [ingredient(name = 'rubber',                  number = 2)],
    #        rate = 20, machine = 'refinery'),

    # recipe(inputs =  [ingredient(name = 'oil',                     number = 6)],
    #        outputs = [ingredient(name = 'fuel',                    number = 4),
    #                   ingredient(name = 'polymer resin',           number = 3, is_primary = False)],
    #        rate = 40, machine = 'refinery'),
    recipe(inputs =  [ingredient(name = 'heavy oil residue',       number = 6)],
           outputs = [ingredient(name = 'fuel',                    number = 4)],
           rate = 40, machine = 'refinery'),

    # recipe(inputs =  [ingredient(name = 'fuel',                    number = 1)],
    #        outputs = [], name='power generation fuel',
    #        rate = 12, machine = 'fuel generator'),
    recipe(inputs =  [ingredient(name = 'turbofuel',               number = 1)],
           outputs = [], name='power generation turbofuel',
           rate = 4.5, machine = 'fuel generator'),

    recipe(inputs =  [ingredient(name = 'fuel',                    number = 6),
                      ingredient(name = 'compacted coal',          number = 4)],
           outputs = [ingredient(name = 'turbofuel',               number = 5)],
           rate = 18.75, machine = 'refinery'),
    recipe(inputs =  [ingredient(name = 'heavy oil residue',       number = 4)],  # TODO no primary recipe for this input
           outputs = [ingredient(name = 'petroleum coke',          number = 12)],
           rate = 120, machine = 'refinery'),
    recipe(inputs =  [ingredient(name = 'copper sheet',            number = 2),
                      ingredient(name = 'plastic',                 number = 4)],
           outputs = [ingredient(name = 'circuit board',           number = 1)],
           rate = 7.5, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'caterium ingot',          number = 1)],
           outputs = [ingredient(name = 'quickwire',               number = 5)],
           rate = 60, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'copper sheet',            number = 5),
                      ingredient(name = 'quickwire',               number = 20)],
           outputs = [ingredient(name = 'ai limiter',              number = 1)],
           rate = 5, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'quartz crystal',          number = 36),
                      ingredient(name = 'cable',                   number = 28),
                      ingredient(name = 'reinforced iron plate',   number = 5)],
           outputs = [ingredient(name = 'crystal oscillator',      number = 2)],
           rate = 1, machine = 'manufacturer'),
    recipe(inputs =  [ingredient(name = 'circuit board',           number = 10),
                      ingredient(name = 'cable',                   number = 9),
                      ingredient(name = 'plastic',                 number = 18),
                      ingredient(name = 'screw',                   number = 52)],
           outputs = [ingredient(name = 'computer',                number = 1)],
           rate = 2.5, machine = 'manufacturer'),
    recipe(inputs =  [ingredient(name = 'motor',                   number = 2),
                      ingredient(name = 'rubber',                  number = 15),
                      ingredient(name = 'smart plating',           number = 2)],
           outputs = [ingredient(name = 'modular engine',          number = 1)],
           rate = 1, machine = 'manufacturer'),
    recipe(inputs =  [ingredient(name = 'automated wiring',        number = 15),
                      ingredient(name = 'circuit board',           number = 10),
                      ingredient(name = 'heavy modular frame',     number = 2),
                      ingredient(name = 'computer',                number = 2)],
           outputs = [ingredient(name = 'adaptive control unit',   number = 2)],
           rate = 1, machine = 'manufacturer'),

    recipe(inputs =  [ingredient(name = 'bauxite',                 number = 12),
                      ingredient(name = 'water',                   number = 18)],
           outputs = [ingredient(name = 'alumina solution',        number = 12),
                      ingredient(name = 'silica',                  number = 5, is_primary = False)],
           rate = 120, machine = 'refinery'),
    recipe(inputs =  [ingredient(name = 'alumina solution',        number = 4),
                      ingredient(name = 'coal',                    number = 2)],
           outputs = [ingredient(name = 'aluminum scrap',          number = 6),
                      ingredient(name = 'water',                   number = 2, is_primary = False)],
           rate = 360, machine = 'refinery'),
    recipe(inputs =  [ingredient(name = 'aluminum scrap',          number = 6),
                      ingredient(name = 'silica',                  number = 5)],
           outputs = [ingredient(name = 'aluminum ingot',          number = 4)],
           rate = 60, machine = 'foundry'),
    recipe(inputs =  [ingredient(name = 'aluminum ingot',          number = 3),
                      ingredient(name = 'copper ingot',            number = 1)],
           outputs = [ingredient(name = 'alclad aluminum sheet',   number = 3)],
           rate = 30, machine = 'assembler'),
    recipe(inputs =  [ingredient(name = 'aluminum ingot',          number = 3)],
           outputs = [ingredient(name = 'aluminum casing',         number = 2)],
           rate = 60, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'aluminum casing',         number = 32),
                      ingredient(name = 'crystal oscillator',      number = 1),
                      ingredient(name = 'computer',                number = 1)],
           outputs = [ingredient(name = 'radio control unit',      number = 2)],
           rate = 2.5, machine = 'manufacturer'),

    # TODO create resource sinks / waste disposal paths
]

raw_inputs = [
    'bauxite',
    'caterium ore',
    'coal',
    'copper ore',
    'iron ore',
    'limestone',
    'oil',
    'quartz',
    'sulfur',
    'water'
]


# data transformations

# verify we don't lose any recipes in the transformation (invalid user configuration)
l, names = len(recipes), [r.name for r in recipes]
recipes = {r.name : r for r in recipes}
assert l == len(recipes), f'Lost {l - len(recipes)} recipes! {sorted(names)}'




# create symbolic variables
Sym_Map = namedtuple('Sym_Map', ['recipes', 'raw_inputs'])

sym_vars = Sym_Map({}, {})  # name to symbolic variable
for name in raw_inputs:
    sym_vars.raw_inputs[name] = sympy.symbols('i_' + re.sub(r'\s+', '_', name))
for name in recipes:
    sym_vars.recipes[name] = sympy.symbols('r_' + re.sub(r'\s+', '_', name))

sym_names = Sym_Map({}, {})  # reverse lookup
for k, v in sym_vars.raw_inputs.items():
    sym_names.raw_inputs[v] = k
for k, v in sym_vars.recipes.items():
    sym_names.recipes[v] = k

all_sym_vars = [v for k,v in sym_vars.recipes.items()] + [v for k,v in sym_vars.raw_inputs.items()]




# target specific product
# target = ingredient(name = 'computer', number = 5)
# target = ingredient(name = 'modular engine', number = 500 / 120)
# target = ingredient(name = 'adaptive control unit', number = 1)
# target = ingredient(name = 'turbofuel', number = 4.5*20)
target = [ingredient(name = 'alclad aluminum sheet', number = sympy.Rational('100')),
          ingredient(name = 'aluminum casing', number = sympy.Rational('100')),
          ingredient(name = 'radio control unit', number = sympy.Rational('5')),
          # ingredient(name = 'aluminum casing', number = sympy.Rational('2.5')),
          # ingredient(name = 'crystal oscillator', number = sympy.Rational('2.5')),
          # ingredient(name = 'computer', number = sympy.Rational('2.5')),
          # ingredient(name = 'circuit board', number = sympy.Rational('2.5')),
          # ingredient(name = 'cable', number = sympy.Rational('2.5')),
          # ingredient(name = 'plastic', number = sympy.Rational('100')),
          # ingredient(name = 'screw', number = sympy.Rational('2.5')),
          ]

target = {ing.name: ing for ing in target}




# the recipes form a system of linear expressions
# so we can set a goal product to form an equation, and solve the system
# the system can be represented as matrices:
#       Recipes            recipe        goal
#      (columns)         multipliers   (column)
# [ -1io   0ii       ]     [  a  ]     [ -x   ]  # raw_inputs get variables
# [  1ii  -3ii  ...  ]  *  [  b  ]  =  [  0   ]  # all other (intermediate product) entries get zeros
# [  0ip   2ip       ]     [  c  ]     [  100 ]  # goal quantity gets user input number
# [     ...          ]     [ ... ]     [  ... ]
# where labels, io = iron ore, ii = iron ingot, and ip = iron plate
# the recipe matrix has
#   columns = one recipe, with inputs as negative numbers and outputs positve
#   rows = one ingredient type (ie iron ore or iron ingot)
# recipe multipliers is a column vector of unique variables
# goal is a column vector of mixed numbers and variables, described inline above

# Finally, sympy seems easier to operate if we simply the system into a set of expressions equal to zero
#   rather than try to have sympy handle the matrices directly
# So we iterate a list of all ingredients, creating one expression for each
expressions = []

for expr_name in all_ingredients:
    expression = 0

    # add terms for each recipe if it includes this ingredient, in inputs or outputs
    for recipe_name, r in recipes.items():
        for ing in r.inputs:
            if ing.name == expr_name:
                expression -= ing.number * sym_vars.recipes[recipe_name]

        for ing in r.outputs:
            if ing.name == expr_name:
                expression += ing.number * sym_vars.recipes[recipe_name]

    # subtract goal value
    #   all cases not covered have goal values of zero, so there is nothing to subbtract
    if expr_name in raw_inputs:
        expression += sym_vars.raw_inputs[expr_name]  # note sign is positive

    elif expr_name in target:
        expression -= target[expr_name].number

    expressions.append(expression)

# solve linear set of equations
solution = sympy.linsolve(expressions, all_sym_vars)
assert solution is not sympy.S.EmptySet
assert len(solution) == 1, f'Did not produce a valid output. linsolve "Returns EmptySet, if the linear system is inconsistent."\n{solution}'

solution = list(solution)[0]  # must cast to list before accessing elements, does not implement pop method
assert len(solution) == len(all_sym_vars)

# cast solution set to floats, from sympy internal (exact) representations
_solution = []
valid_types = [  # for conversion to float
    sympy.core.numbers.Zero,
    sympy.core.numbers.Rational,
    sympy.core.numbers.Integer,
]
for val in solution:
    assert type(val) in valid_types, f'unsupported type, {type(val)}, {val}'
    _solution.append(float(val))

# convert solution to list of production steps
#   solution is ordered in order of all_sym_vars
# iterate solution in multiple steps, since it contains both raw_inputs and recipe_multipliers which are handled differently
steps = []
i_sym_var = 0
for _ in range(len(sym_vars.recipes)):
    sym_var = all_sym_vars[i_sym_var]
    recipe_multiplier = solution[i_sym_var]

    recipe_name = sym_names.recipes[sym_var]
    r = recipes[recipe_name]

    if r.primary_output is not None:
        output_number = r.primary_output.number
    else:
        output_number = 1  # do not scale recipes with zero outputs, by output rate

    if recipe_multiplier != 0:
        steps.append(ingredient(name = r.name, number = output_number * recipe_multiplier))

    i_sym_var += 1

for _ in range(len(sym_vars.raw_inputs)):
    sym_var = all_sym_vars[i_sym_var]
    number = solution[i_sym_var]
    name = sym_names.raw_inputs[sym_var]

    if number != 0:
        steps.append(ingredient(name = name, number = number))

    i_sym_var += 1




# outfit steps with additional pruoduction line info
production_lines = [production_line(step) for step in steps]

# reverse topologically sort production lines
#   ignore excess outputs to avoid cyclical dependancies
#   always put raw_inputs first, regardless of when they are liberated in the topology
_production_lines = []
raw_input_lines = [line for line in production_lines if line.ing.name in raw_inputs]
production_lines = [line for line in production_lines if line.ing.name not in raw_inputs]
while production_lines:
    # collect list of lines with no incoming dependancy edges
    depended_upon = {ing.name for line in production_lines for ing in line.inputs}
    not_depended_upon = [line for line in production_lines if line.ing.name not in depended_upon]
    assert len(not_depended_upon) > 0, f'Failed to find any nodes without dependancies, {production_lines}'

    # sort this subset of production lines, insert them into the new list, and clear from the original list
    not_depended_upon.sort(key=lambda x: x.sort_key, reverse=True)
    _production_lines += not_depended_upon
    production_lines = [line for line in production_lines if line not in not_depended_upon]

_production_lines += sorted(raw_input_lines, key=lambda x: x.sort_key, reverse=True)
production_lines = list(reversed(_production_lines))

# print production lines
print(f'Production Lines ({len(production_lines)})')
for line in production_lines:
    print(str(line))

