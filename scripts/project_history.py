"""Portable, explicit revision snapshots and comparisons of generated projects."""
import hashlib
import json
from collections import Counter
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def snapshot(project, boards, cost, version):
    def fields(obj, keys):
        return {key: obj.get(key) for key in keys}
    panels = {p['id']: fields(p, ('name', 'material', 'origin_mm', 'size_mm', 'panel_axes', 'bands_mm', 'grain', 'allow_rotation', 'group')) for p in project['parts']}
    materials = {key: fields(m, ('name', 'kind', 'thickness_mm', 'color', 'stock')) for key, m in project['materials'].items()}
    cost_data = None if cost is None else {
        'priced_subtotal_eur': cost.get('estimated_priced_subtotal_eur'),
        'status': cost.get('status'), 'as_of_date': cost.get('as_of_date'),
        'basis_sha256': digest(cost.get('rows', [])),
    }
    result = dict(schema_version=1, kind='furniture-revision', name=project['name'], generator_version=version,
                  parts=panels, materials=materials, fittings={p['id']: p for p in project.get('fittings', [])},
                  board_counts=dict(Counter(b['material'] for b in boards)), cost=cost_data,
                  decisions_sha256=digest({k: project.get(k) for k in ('confirmed', 'assumptions', 'intake_review', 'dimension_annotations')}),
                  project_sha256=digest(project))
    result['snapshot_sha256'] = digest(result)
    return result


def load_snapshot(path):
    path = Path(path)
    if path.is_dir():
        path = path / 'revision.json'
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or value.get('kind') != 'furniture-revision' or value.get('schema_version') != 1:
        raise ValueError('Expected a furniture revision.json snapshot')
    stored = value.get('snapshot_sha256')
    if stored != digest({k: v for k, v in value.items() if k != 'snapshot_sha256'}):
        raise ValueError('Revision snapshot hash mismatch')
    return value


def compare(previous, current):
    changes = {}
    for section in ('parts', 'materials', 'fittings'):
        old, new = previous[section], current[section]
        changes[section] = dict(added=sorted(new.keys() - old.keys()), removed=sorted(old.keys() - new.keys()),
                               changed=[dict(id=key, fields=sorted(k for k in old[key].keys() | new[key].keys() if old[key].get(k) != new[key].get(k)), before=old[key], after=new[key])
                                        for key in sorted(old.keys() & new.keys()) if old[key] != new[key]])
    boards = [dict(material=key, before=previous['board_counts'].get(key, 0), after=current['board_counts'].get(key, 0))
              for key in sorted(previous['board_counts'].keys() | current['board_counts'].keys())]
    old_cost, new_cost = previous.get('cost'), current.get('cost')
    cost = dict(before=old_cost, after=new_cost, delta_priced_subtotal_eur=None)
    if old_cost and new_cost and all(isinstance(c.get('priced_subtotal_eur'), (int, float)) for c in (old_cost, new_cost)):
        from decimal import Decimal
        cost['delta_priced_subtotal_eur'] = float(Decimal(str(new_cost['priced_subtotal_eur'])) - Decimal(str(old_cost['priced_subtotal_eur'])))
    return dict(schema_version=1, previous_sha256=previous['snapshot_sha256'], current_sha256=current['snapshot_sha256'],
                previous_version=previous['generator_version'], current_version=current['generator_version'],
                changes=changes, boards=boards, cost=cost,
                decisions_changed=previous['decisions_sha256'] != current['decisions_sha256'],
                note='Priced material subtotal only, not a final quote. Check price dates, included items and completeness independently. Snapshot hashes detect changes, not authenticity or approval.')
