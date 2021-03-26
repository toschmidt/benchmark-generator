import copy
import importlib
import json
import os

from jsonschema import validate
from jinja2 import Template

from .parameter_generators import parameter_generators


def read_benchmark(path: str):
    directory = os.path.dirname(path)

    with open(path) as json_file:
        benchmark = json.load(json_file)
        assert ('$schema' in benchmark)
        schema_path = os.path.join(directory, benchmark['$schema'])
        with open(schema_path) as schema_file:
            schema = json.load(schema_file)
            validate(instance=benchmark, schema=schema)
            return benchmark, schema, os.path.dirname(schema_path)


def merge(object1, object2, key: str):
    if key not in object1:
        object1[key] = copy.deepcopy(object2[key])
    else:
        if isinstance(object2[key], dict):
            for subkey in object2[key].keys():
                if subkey not in object1[key]:
                    object1[key][subkey] = copy.deepcopy(object2[key][subkey])
    return object1


def execute_argument_generator(name, arguments, schema_dir):
    generator = parameter_generators[name]
    if generator['path'] is None:
        return generator['method'](**arguments)
    else:
        spec = importlib.util.spec_from_file_location(generator['method'], os.path.join(schema_dir, generator['path']))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, generator['method'])(**arguments)


def write_benchmark(template: str, cpp: str, benchmarks):
    if not os.path.exists(os.path.dirname(cpp)):
        os.makedirs(os.path.dirname(cpp))

    with open(template) as template_file:
        with open(cpp, 'w') as cpp_file:
            template = Template(template_file.read(), trim_blocks=True, lstrip_blocks=True)
            cpp_file.write(template.render(benchmarks=benchmarks))


def generate_benchmark(benchmark: str, cpp: str):
    definition, schema, schema_dir = read_benchmark(benchmark)
    template = os.path.join(schema_dir, schema['data']['template'])

    for generator_name, generator_value in schema['data']['generators'].items():
        assert (generator_name not in parameter_generators)
        parameter_generators[generator_name] = generator_value

    benchmarks = []

    for benchmark in definition['benchmarks']:
        benchmark = merge(benchmark, definition, 'parameters')

        for parameter_name, parameter_value in benchmark['parameters'].items():
            if isinstance(parameter_value, dict) and 'generator' in parameter_value:
                assert (parameter_value['generator'] in parameter_generators)
                benchmark['parameters'][parameter_name] = execute_argument_generator(parameter_value['generator'],
                                                                                     parameter_value['attributes'],
                                                                                     schema_dir)

        benchmarks.append(benchmark)

    write_benchmark(template, cpp, benchmarks)
