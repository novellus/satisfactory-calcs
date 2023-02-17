# imports
import re
from collections import defaultdict


# base classes
class recipe():
    def __init__(self, inputs, outputs, rate, machine):
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

    def copy(self):
        return recipe([x.copy() for x in self.inputs], [x.copy() for x in self.outputs], self.rate, self.machine)


class ingredient():
    def __init__(self, name, number, end_point=False, is_primary=True, sub_ingredients=None, is_waste=False):
        self.name = name
        self.number = number
        self.end_point = end_point
        self.is_primary = is_primary  # only relevant for recipe outputs
        self.sub_ingredients = sub_ingredients  # only used when recursively defined

        # set / read by production line
        self.is_waste = is_waste

    def copy(self):
        if self.sub_ingredients is None:
            new_sub_ingredients = None
        else:
            new_sub_ingredients = [x.copy() for x in self.sub_ingredients]

        return ingredient(self.name, self.number, self.end_point, self.is_primary, new_sub_ingredients, self.is_waste)

    def __str__(self):
        return f'Ingredient: {self.number} x {self.name}, end_point: {self.end_point}, is_primary: {self.is_primary}, is_waste: {self.is_waste}, sub_ingredients is None: {self.sub_ingredients is None}'


class production_line():
    def __init__(self, ing):
        self.ing = ing.copy()

        if not self.ing.end_point:
            self.recipe = recipes[self.ing.name]
            self.num_machines = self.ing.number / self.recipe.rate
            self.sort_key = (machine_order.index(self.recipe.machine), -self.ing.number, self.ing.name)

            self.excess_outputs = [ing.copy() for ing in self.recipe.outputs if not ing.is_primary]
            scale_factor = self.ing.number / self.recipe.primary_output.number
            for ing in self.excess_outputs:
                ing.number *= scale_factor

            add_sub_ingredients(self.ing, max_recursion_depth = 1)  # compute only the direct ingredients

        else:
            self.sort_key = (-1, -self.ing.number, self.ing.name)

    def __str__(self):
        if self.ing.end_point:
            s = 'Raw Input: '
        else:
            s = 'Line: '

        s += f'{self.ing.number:.1f} x {self.ing.name}'
        
        if not self.ing.end_point:
            s += f' ({self.num_machines:.1f} x {self.recipe.machine})'
            for ing in self.excess_outputs:
                s += f'\n    '

                if ing.is_waste:
                    s += f'Waste: '
                else:
                    s += f'Recycle: '

                s += f'{ing.number:.1f} x {ing.name}'
            for ing in self.ing.sub_ingredients:
                s += f'\n    Ingredient: {ing.number:.1f} x {ing.name}'
        
        return s


machine_order = ['smelter', 'foundry', 'refinery', 'constructor', 'assembler', 'manufacturer', 'packager']


# recipes
# comment out alternative recipies to remove pathways
recipes = [
    recipe(inputs =  [ingredient(name = 'iron ore',                number = 1, end_point=True)],
           outputs = [ingredient(name = 'iron ingot',              number = 1)],
           rate = 30, machine = 'smelter'),

    # recipe(inputs =  [ingredient(name = 'copper ore',              number = 1, end_point=True)],
    #        outputs = [ingredient(name = 'copper ingot',            number = 1)],
    #        rate = 30, machine = 'smelter'),
    recipe(inputs =  [ingredient(name = 'copper ore',              number = 6, end_point=True),
                      ingredient(name = 'water',                   number = 4, end_point=True)],
           outputs = [ingredient(name = 'copper ingot',            number = 15)],
           rate = 37.5, machine = 'refinery'),

    recipe(inputs =  [ingredient(name = 'caterium ore',            number = 3, end_point=True)],
           outputs = [ingredient(name = 'caterium ingot',          number = 1)],
           rate = 15, machine = 'smelter'),

    recipe(inputs =  [ingredient(name = 'iron ore',                number = 3, end_point=True),
                      ingredient(name = 'coal',                    number = 3, end_point=True)],
           outputs = [ingredient(name = 'steel ingot',             number = 3)],
           rate = 45, machine = 'foundry'),
    # recipe(inputs =  [ingredient(name = 'iron ore',                number = 6, end_point=True),
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

    # recipe(inputs =  [ingredient(name = 'copper ingot',            number = 1)],
    #        outputs = [ingredient(name = 'wire',                    number = 2)],
    #        rate = 30, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'iron ingot',              number = 5)],
           outputs = [ingredient(name = 'wire',                    number = 9)],
           rate = 22.5, machine = 'constructor'),

    recipe(inputs =  [ingredient(name = 'wire',                    number = 2)],
           outputs = [ingredient(name = 'cable',                   number = 1)],
           rate = 30, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'limestone',               number = 3, end_point=True)],
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
    recipe(inputs =  [ingredient(name = 'quartz',                  number = 5, end_point=True)],
           outputs = [ingredient(name = 'quartz crystal',          number = 3)],
           rate = 22.5, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'quartz',                  number = 3, end_point=True)],
           outputs = [ingredient(name = 'silica',                  number = 5)],
           rate = 37.5, machine = 'constructor'),
    recipe(inputs =  [ingredient(name = 'coal',                    number = 1, end_point=True),
                      ingredient(name = 'sulfur',                  number = 1, end_point=True)],
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

    recipe(inputs =  [ingredient(name = 'steel beam',              number = 4),
                      ingredient(name = 'concrete',                number = 5)],
           outputs = [ingredient(name = 'encased industrial beam', number = 1)],
           rate = 6, machine = 'assembler'),
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
    recipe(inputs =  [ingredient(name = 'coal',                    number = 5, end_point = True),
                      ingredient(name = 'sulfur',                  number = 5, end_point = True)],
           outputs = [ingredient(name = 'compacted coal',          number = 5)],
           rate = 25, machine = 'assembler'),

    recipe(inputs =  [ingredient(name = 'oil',                     number = 3, end_point = True)],
           outputs = [ingredient(name = 'plastic',                 number = 2),
                      ingredient(name = 'heavy oil residue',       number = 1, is_primary = False)],
           rate = 20, machine = 'refinery'),
    # recipe(inputs =  [ingredient(name = 'polymer resin',           number = 6),
    #                   ingredient(name = 'water',                   number = 2, end_point=True)],
    #        outputs = [ingredient(name = 'plastic',                 number = 2)],
    #        rate = 20, machine = 'refinery'),

    recipe(inputs =  [ingredient(name = 'oil',                     number = 3, end_point = True)],
           outputs = [ingredient(name = 'rubber',                  number = 2),
                      ingredient(name = 'heavy oil residue',       number = 2, is_primary = False)],
           rate = 20, machine = 'refinery'),
    # recipe(inputs =  [ingredient(name = 'polymer resin',           number = 4),
    #                   ingredient(name = 'water',                   number = 4, end_point=True)],
    #        outputs = [ingredient(name = 'rubber',                  number = 2)],
    #        rate = 20, machine = 'refinery'),

    recipe(inputs =  [ingredient(name = 'oil',                     number = 6, end_point = True)],
           outputs = [ingredient(name = 'fuel',                    number = 4),
                      ingredient(name = 'polymer resin',           number = 3, is_primary = False)],
           rate = 40, machine = 'refinery'),
    # recipe(inputs =  [ingredient(name = 'heavy oil residue',       number = 6)],
    #        outputs = [ingredient(name = 'fuel',                    number = 4)],
    #        rate = 40, machine = 'refinery'),

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
    recipe(inputs =  [ingredient(name = 'quarts crystal',          number = 36),
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

    recipe(inputs =  [ingredient(name = 'bauxite',                 number = 12, end_point = True),
                      ingredient(name = 'water',                   number = 18, end_point = True)],
           outputs = [ingredient(name = 'alumina solution',        number = 12),
                      ingredient(name = 'silica',                  number = 5, is_primary = False)],
           rate = 120, machine = 'refinery'),
    recipe(inputs =  [ingredient(name = 'alumina solution',        number = 4),
                      ingredient(name = 'coal',                    number = 2, end_point = True)],
           outputs = [ingredient(name = 'aliminum scrap',          number = 6),
                      ingredient(name = 'water',                   number = 2, is_primary = False)],
           rate = 360, machine = 'refinery'),
    recipe(inputs =  [ingredient(name = 'aliminum scrap',          number = 6),
                      ingredient(name = 'silica',                  number = 5)],
           outputs = [ingredient(name = 'aluminum ingot',          number = 4)],
           rate = 60, machine = 'foundry'),
]


# data transformations
recipes = {r.primary_output.name : r for r in recipes}


def add_sub_ingredients(ing, max_recursion_depth = float('inf')):
    # modifies ing in place, adding attribute sub_ingredients, recursively
    # where sub_ingredients is a list of ingredient objects, with number scaled by the respective recipe to create the given number of input ing

    ing.sub_ingredients = []

    if not ing.end_point and max_recursion_depth > 0:
        # extract and scale target recipe
        r = recipes[ing.name].copy()
        scale_factor = ing.number / r.primary_output.number

        for sub_ingredient in r.inputs:
            sub_ingredient.number *= scale_factor
            add_sub_ingredients(sub_ingredient, max_recursion_depth - 1)
            ing.sub_ingredients.append(sub_ingredient)


def consolidate_production_steps(ing):
    # execute after add_sub_ingredients function
    # returns dict {name: ingredient}, for each ingredient recursively consolidated from the sub_ingredients attribute of ing
    #   adds ingredient numbers
    #   sets sub_ingredients attributes to None 

    steps = {ing.name : ing.copy()}
    steps[ing.name].sub_ingredients = None  # wipe sub_ingredients from consolidated list

    if not ing.end_point:
        for sub_ingredient in ing.sub_ingredients:
            sub_steps = consolidate_production_steps(sub_ingredient)

            for name, sub_ingredient in sub_steps.items():
                if name not in steps:
                    steps[name] = sub_ingredient.copy()
                    steps[name].sub_ingredients = None  # wipe sub_ingredients from consolidated list
                else:
                    steps[name].number += sub_ingredient.number

    return steps


def balance_io(production_lines):
    # subtracts excess outputs in each production line from the line producing that item, if any
    # TODO finish this.
    #   Every time an excess is removed, excesses need to be recomputed throughout, and recursive recipe changes need to be resolved
    #   probably need to just use an linear-algebraic solver
    
    lines = {line.ing.name: line for line in production_lines}
    excess_outputs = []
    for line in production_lines:
        if not line.ing.end_point:
            for ing in line.excess_outputs:
                excess_outputs.append(ing)

    def modify_line(name, delta):
        # delta is real number, typically less than zero, as a change to the named production line primary output number
        # recursively modifies the output requirements of the named production line, and its dependancies

        # compute modified production line
        orig_line = lines[name]
        line_ing = orig_line.ing.copy()
        line_ing.number -= delta
        new_line = production_line(line_ing)

        # compute differences for line ingredients

        lines[name] = new_line

    for excess_ing in excess_outputs:
        if excess_ing.name not in lines:
            excess_ing.is_waste = True

        else:
            # TODO this needs to be recursive on ingredients...
            modify_line(excess_ing.name, excess_ing.number)

    return [v for k,v in lines.items()]




# target specific product
# target = ingredient(name = 'computer', number = 5)
# target = ingredient(name = 'modular engine', number = 500 / 120)
# target = ingredient(name = 'adaptive control unit', number = 1)
# target = ingredient(name = 'turbofuel', number = 4.5*20)
target = ingredient(name = 'aluminum ingot', number = 100)

# construct product tree
add_sub_ingredients(target)

# consolidate production steps
steps = consolidate_production_steps(target)

# order steps, and outfit with additional information
production_lines = [production_line(v) for k,v in steps.items()]
# production_lines = balance_io(production_lines)  # TODO
production_lines.sort(key=lambda x: x.sort_key)

# print formatted full tree
# print('Product Tree')
# def pretty_print(ing, depth = 0):
#     print("    " * depth + f'{ing.name} x {ing.number}')
#     if not ing.end_point:
#         for sub_ingredient in ing.sub_ingredients:
#             pretty_print(sub_ingredient, depth = depth + 1)
# pretty_print(target)
# print()

# print production lines
print(f'Production Lines ({len(production_lines)})')
for line in production_lines:
    print(str(line))

