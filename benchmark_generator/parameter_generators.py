def range_generator(min: int, max: int, step: int):
    return list(range(min, max + 1, step))


parameter_generators = {
    'range': {
        'path': None,
        'method': range_generator,
        'attributes': {
            'min': {
                'type': 'integer'
            },
            'max': {
                'type': 'integer'
            },
            'step': {
                'type': 'integer'
            }
        }
    }
}
