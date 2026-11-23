"""Review metadata derived from generated geometry, never manufacturing approval."""
import math


def dimension_annotations(project):
    parts = {p['id']: p for p in project['parts']}
    result, seen = [], set()
    for item in project.get('dimension_annotations', []):
        identifier = item['id']
        axis = item['axis']
        if not isinstance(identifier, str) or identifier in seen or not identifier:
            raise ValueError('Dimension annotation IDs must be unique strings')
        if type(axis) is not int or axis not in (0, 1, 2):
            raise ValueError('Dimension annotation axis must be 0, 1 or 2')
        seen.add(identifier)
        try:
            start_part, end_part = parts[item['start_part']], parts[item['end_part']]
        except KeyError as error:
            raise ValueError('Dimension annotation refers to an unknown part') from error
        if item['start_face'] not in ('min', 'max') or item['end_face'] not in ('min', 'max'):
            raise ValueError('Dimension annotation face must be min or max')
        a = [start_part['origin_mm'][k] + start_part['size_mm'][k] / 2 for k in range(3)]
        a[axis] = start_part['origin_mm'][axis] + (start_part['size_mm'][axis] if item['start_face'] == 'max' else 0)
        b = a.copy()
        b[axis] = end_part['origin_mm'][axis] + (end_part['size_mm'][axis] if item['end_face'] == 'max' else 0)
        distance = b[axis] - a[axis]
        if not math.isfinite(distance) or distance <= 0:
            raise ValueError('Dimension annotation must measure a positive clear distance')
        result.append(dict(id=identifier, label=str(item.get('label', identifier)), start_mm=a, end_mm=b, value_mm=distance))
    return result


def review_metadata(project, boards, cost, png_previews):
    assumptions = project.get('assumptions', [])
    excluded = [p['id'] for p in project['parts'] if not project['materials'][p['material']].get('stock')]
    stages = [
        dict(id='specification', label='Размери и решения', status='review', detail=f'{len(assumptions)} допускания за преглед' if assumptions else 'Няма записани допускания; потвърждението от мебелиста остава отделна стъпка', tab='assumptions-view'),
        dict(id='geometry', label='Панелен модел', status='prepared', detail=f'{len(project["parts"])} детайла; геометричните проверки преминаха', tab='parts'),
        dict(id='preview', label='Визуализация', status='prepared', detail='3D преглед' + (' и два PNG изгледа' if png_previews else '; PNG изображения не са генерирани'), tab='model'),
        dict(id='nesting', label='Предварителен разкрой', status='partial' if excluded else 'prepared', detail=f'{len(boards)} плоскости; {len(excluded)} детайла без складов формат' if excluded else f'{len(boards)} плоскости; включените детайли са разположени', tab='cutting'),
        dict(id='cost', label='Материали и стойност', status='partial' if cost else 'pending', detail='Ориентировъчна калкулация; цените и комплектността подлежат на проверка' if cost else 'Няма приложена калкулация', tab='cost'),
        dict(id='production', label='Проверка преди рязане', status='pending', detail='Мебелистът проверява сглобки, кантове, обков и допуски', tab='assumptions-view'),
    ]
    return dict(stages=stages, assumption_count=len(assumptions), excluded_part_ids=excluded, dimensions=dimension_annotations(project), production_approved=False)
