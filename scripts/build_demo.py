#!/usr/bin/env python3
"""Build a mobile-friendly gallery from explicitly selected public projects."""
import html
import json
from pathlib import Path
import re
import shutil
import tempfile
import furniture

ROOT = Path(__file__).resolve().parents[1]


def entries(root):
    items = json.loads((root / 'public-projects.json').read_text())
    if not isinstance(items, list) or not items:
        raise ValueError('The public gallery must contain at least one project')
    seen = set()
    result = []
    for item in items:
        pid = item['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', pid) or pid in seen:
            raise ValueError('Invalid or duplicate public project ID')
        seen.add(pid)
        path = (root / item['source']).resolve()
        if not path.is_relative_to((root / 'examples').resolve()) or not path.is_file():
            raise ValueError('Only explicit example files may be published')
        project = json.loads(path.read_text())
        text = json.dumps(project, ensure_ascii=False)
        if project.get('source_image') or project.get('source_conversation') or any(
            token in text for token in ('chatgpt.com/share/', '/Users/', '/Applications/', 'file://')
        ):
            raise ValueError('Remove private provenance from the public example')
        result.append((item, project))
    return result


def build(root=ROOT):
    selected = entries(root)  # Validate every input before touching the old gallery.
    work = root / 'work'
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gallery-', dir=work) as tmp:
        staging = Path(tmp) / 'site'
        staging.mkdir()
        cards = []
        for item, project in selected:
            pid = item['id']
            project['name'] = item['title']
            project['subtitle'] = item['summary']
            project['demo'] = True
            source = Path(tmp) / f'{pid}.json'
            source.write_text(json.dumps(project, ensure_ascii=False, indent=2))
            output = staging / 'projects' / pid
            baseline = None
            if item.get("compare_to"):
                baseline = (root / item["compare_to"]).resolve()
                if not baseline.is_relative_to((root / "examples").resolve()) or not baseline.is_file():
                    raise ValueError("Public comparison must use an explicit example snapshot")
            furniture.build(source, output, baseline)
            image = f'<img src="projects/{pid}/exterior.png" alt="Външен изглед" loading="lazy">' if (output / 'exterior.png').exists() else ''
            cards.append(f'<a class="card" href="projects/{pid}/"><div class="image">{image}</div><div class="copy"><span>ПРЕДВАРИТЕЛЕН ПРОЕКТ</span><h2>{html.escape(item["title"])}</h2><p>{html.escape(item["summary"])}</p><strong>Разгледай проекта →</strong></div></a>')
        page = '''<!doctype html><html lang="bg"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sketch to Furniture · Проекти</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf1f1;color:#20343d;font:17px/1.55 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:clamp(20px,5vw,64px)}header{max-width:750px;margin-bottom:42px}.eyebrow,span{font-size:12px;letter-spacing:.13em;color:#516c76}h1{font-size:clamp(34px,6vw,62px);line-height:1.1;margin:18px 0}p{color:#53666e}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:24px}.card{display:block;text-decoration:none;color:inherit;border:1px solid #d0dcdc;background:#fff;border-radius:16px;overflow:hidden}.card:hover,.card:focus-visible{outline:3px solid #7299a6}.image{background:#e3e8e7}.image img{display:block;width:100%;max-height:360px;object-fit:contain}.copy{padding:26px}h2{font-size:25px;line-height:1.25;margin:12px 0}strong{color:#246377}footer{margin-top:40px;font-size:14px}footer a{color:#246377}
</style></head><body><main><header><div class="eyebrow">SKETCH TO FURNITURE / ГАЛЕРИЯ</div><h1>От скица до мебел.</h1><p>Разгледайте проекта отвън и отвътре, размерите, материалите и предварителния разкрой. Отворете избрания модел от телефон или компютър.</p></header><section class="grid">CARDS</section><footer><p>Проектите са предварителни. Цветовете са приблизителни; точните декори се сверяват с физическа мостра. Разкроят изисква проверка на конструкцията и обкова.</p><a href="https://github.com/plamen911/sketch-to-furniture">Код и инструкции</a> · <a href="https://plamen.lynxlake.org/">Plamen Markov</a></footer></main></body></html>'''
        (staging / 'index.html').write_text(page.replace('CARDS', ''.join(cards)))
        (staging / '.nojekyll').write_text('')
        target = root / 'dist/demo'
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            shutil.rmtree(target)  # Generated site only, after successful builds.
        shutil.move(str(staging), str(target))
    print(f'Built gallery with {len(selected)} project(s): {target}')


if __name__ == '__main__':
    build()
