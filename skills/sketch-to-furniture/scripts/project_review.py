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
    intake = intake_rows(project)
    conflicts = sum(row['status'] == 'conflict' for row in intake)
    excluded = [p['id'] for p in project['parts'] if not project['materials'][p['material']].get('stock')]
    stages = [
        dict(id='specification', label='Размери и решения', status='review', detail=f'{len(intake)} записа · {conflicts} несъответствия · {len(assumptions)} допускания' if intake else (f'{len(assumptions)} допускания за преглед' if assumptions else 'Няма записани допускания; потвърждението от мебелиста остава отделна стъпка'), tab='intake' if intake else 'assumptions-view'),
        dict(id='geometry', label='Панелен модел', status='prepared', detail=f'{len(project["parts"])} детайла; геометричните проверки преминаха', tab='parts'),
        dict(id='preview', label='Визуализация', status='prepared', detail='3D преглед' + (' и два PNG изгледа' if png_previews else '; PNG изображения не са генерирани'), tab='model'),
        dict(id='nesting', label='Предварителен разкрой', status='partial' if excluded else 'prepared', detail=f'{len(boards)} плоскости; {len(excluded)} детайла без складов формат' if excluded else f'{len(boards)} плоскости; включените детайли са разположени', tab='cutting'),
        dict(id='cost', label='Материали и стойност', status='partial' if cost else 'pending', detail='Ориентировъчна калкулация; цените и комплектността подлежат на проверка' if cost else 'Няма приложена калкулация', tab='cost'),
        dict(id='production', label='Проверка преди рязане', status='pending', detail='Мебелистът проверява сглобки, кантове, обков и допуски', tab='assumptions-view'),
    ]
    return dict(stages=stages, assumption_count=len(assumptions), excluded_part_ids=excluded, dimensions=dimension_annotations(project), intake=intake, exploded=exploded_parts(project), production_approved=False)


def intake_rows(project):
    """Reconcile human transcription with live geometric values without inventing confirmation."""
    parts = {p['id']: p for p in project['parts']}
    dims = {d['id']: d['value_mm'] for d in dimension_annotations(project)}
    result, seen = [], set()
    for row in project.get('intake_review', []):
        if not isinstance(row.get('id'), str) or row['id'] in seen:
            raise ValueError('Intake review IDs must be unique strings')
        seen.add(row['id'])
        if row.get('status') not in ('confirmed', 'assumed', 'unclear'):
            raise ValueError('Intake status must be confirmed, assumed or unclear')
        for key in ('label', 'observed_text', 'source'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError('Intake rows require label, observed_text and source')
        interpreted = row.get('interpreted_value')
        if isinstance(interpreted, bool) or not isinstance(interpreted, (str, int, float)) or isinstance(interpreted, (int, float)) and not math.isfinite(interpreted):
            raise ValueError('Intake interpretation must be text or a finite number')
        b = row['binding']
        try:
            if b['kind'] == 'overall':
                axis = b['axis']
                if type(axis) is not int or axis not in (0, 1, 2):
                    raise ValueError('Invalid intake dimension axis')
                bounds = project.get('design_bounds_mm')
                current = bounds['max'][axis] - bounds['min'][axis] if bounds else max(p['origin_mm'][axis] + p['size_mm'][axis] for p in parts.values()) - min(p['origin_mm'][axis] for p in parts.values())
            elif b['kind'] == 'clearance':
                current = dims[b['id']]
            elif b['kind'] == 'material':
                if b['field'] not in ('name', 'thickness_mm', 'color'):
                    raise ValueError('Unsupported intake material field')
                current = project['materials'][b['material']][b['field']]
            elif b['kind'] == 'part_count':
                if len(set(b['ids'])) != len(b['ids']) or any(pid not in parts for pid in b['ids']):
                    raise ValueError('Intake count refers to duplicate or unknown parts')
                current = len(b['ids'])
            else:
                raise ValueError('Unsupported intake binding')
        except (KeyError, TypeError) as error:
            raise ValueError('Invalid intake review binding') from error
        consistent = math.isclose(interpreted, current, abs_tol=1e-6, rel_tol=0) if isinstance(interpreted, (int, float)) and isinstance(current, (int, float)) else interpreted == current
        result.append(dict(id=row['id'], label=row['label'], observed_text=row['observed_text'], source=row['source'], interpreted_value=interpreted,
                           model_value=current, unit=row.get('unit', ''), declared_status=row['status'], status=row['status'] if consistent else 'conflict', consistent=consistent))
    return result


def exploded_parts(project):
    """Return display-only offsets and within-revision numbers; never mutate production geometry."""
    parts = project['parts']
    lo = [min(p['origin_mm'][k] for p in parts) for k in range(3)]
    hi = [max(p['origin_mm'][k] + p['size_mm'][k] for p in parts) for k in range(3)]
    centre = [(a + b) / 2 for a, b in zip(lo, hi)]
    gap = max(60, min(220, max(b-a for a, b in zip(lo, hi)) * 0.07))
    result = []
    for number, p in enumerate(sorted(parts, key=lambda p: p['id']), 1):
        middle = [p['origin_mm'][k] + p['size_mm'][k] / 2 for k in range(3)]
        axis = next(k for k in range(3) if k not in p['panel_axes'])
        offset = [(middle[k] - centre[k]) * 0.35 for k in range(3)]
        offset[axis] += gap * (-1 if middle[axis] < centre[axis] else 1)
        result.append(dict(number=number, part_id=p['id'], name=p['name'], offset_mm=offset))
    return result
