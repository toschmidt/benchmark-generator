import json

from jsonschema import validate
import pkgutil

from .parameter_generators import parameter_generators


def read_definition(path: str):
    data = pkgutil.get_data(__name__, '../benchmark-definition.schema.json')
    schema = json.loads(data.decode('utf-8'))

    with open(path) as json_file:
        definition = json.load(json_file)
        validate(instance=definition, schema=schema)
        return definition


def write_schema(schema, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(schema, f)


def generate_schema(definition: str, out: str):
    definition = read_definition(definition)

    schema = {
        '$schema': 'https://json-schema.org/draft-07/schema',
        'title': 'Benchmark Schema',
        'type': 'object',
        'definitions': {
            'generated-attribute': {
                'anyOf': []
            },
            'parameters': {
                'type': 'object',
                'properties': {},
                'additionalProperties': False
            }
        },
        'properties': {
            '$schema': {'type': 'string'},
            'type': {'type': 'string', 'const': 'benchmark'},
            'name': {'type': 'string'},
            'parameters': {'$ref': '#/definitions/parameters'},
            'benchmarks': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'parameters': {'$ref': '#/definitions/parameters'}
                    },
                    'required': [],
                    'additionalProperties': False
                }
            }
        },
        'required': ['$schema', 'type', 'name', 'parameters', 'benchmarks'],
        'additionalProperties': False,
        'data': {
            'template': definition['template'],
            'generators': definition['generators']
        }
    }

    for key, value in definition['arguments'].items():
        attribute_schema = {
            'type': value['type'],
        }
        if 'enum' in value:
            attribute_schema['enum'] = value['enum']

        schema['properties']['benchmarks']['items']['properties'][key] = {
            'anyOf': [
                attribute_schema,
                {'type': 'array', 'items': attribute_schema, 'minItems': 1}
            ]
        }
        schema['properties']['benchmarks']['items']['required'].append(key)

    for key, value in dict(definition['generators'], **parameter_generators).items():
        generator = {
            'type': 'object',
            'properties': {
                'generator': {
                    'type': 'string',
                    'const': key
                },
                'attributes': {
                    'type': 'object',
                    'properties': {},
                    'required': [],
                    'additionalProperties': False
                },
            },
            'required': ['generator', 'attributes'],
            'additionalProperties': False
        }

        for attribute_name, attribute_value in value['attributes'].items():
            attribute_schema = {
                'type': attribute_value['type'],
            }
            if 'enum' in attribute_value:
                attribute_schema['enum'] = attribute_value['enum']

            generator['properties']['attributes']['properties'][attribute_name] = attribute_schema
            generator['properties']['attributes']['required'].append(attribute_name)

        schema['definitions']['generated-attribute']['anyOf'].append(generator)

    for key, value in definition['parameters'].items():
        parameter_schema = {
            'type': 'array',
            'items': {
            }
        }

        if value['type'] == 'grouped':
            parameter_schema['items']['type'] = 'object'
            parameter_schema['items']['properties'] = {}
            parameter_schema['items']['required'] = []

            for attribute_name, attribute_value in value.items():
                if attribute_name != 'type':
                    parameter_schema['items']['properties'][attribute_name] = {'type': attribute_value['type']}
                    if 'enum' in attribute_value['type']:
                        parameter_schema['items']['properties'][attribute_name]['enum'] = attribute_value['enum']
                    parameter_schema['items']['required'].append(attribute_name)
        else:
            parameter_schema['items']['type'] = value['type']
            if 'enum' in value:
                parameter_schema['items']['enum'] = value['enum']

        schema['definitions']['parameters']['properties'][key] = {
            'anyOf': [
                {
                    '$ref': '#/definitions/generated-attribute'
                },
                parameter_schema
            ]
        }

    write_schema(schema, out)
