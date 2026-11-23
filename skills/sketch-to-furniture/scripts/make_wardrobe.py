#!/usr/bin/env python3
"""Compile the client's confirmed wardrobe specification to explicit panels."""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def make_project():
    W, H, D, T = 1200, 2200, 600, 18
    # Coordinates: X right, Y rearward, Z up. Overall depth includes fronts/back.
    front_y, carcass_y, back_y = 0, 20, 597
    cd = back_y - carcass_y
    left_x, right_x, clear = 18, 609, 573
    parts = []

    def part(
        pid, name, origin, size, axes, material="white", group="carcass", bands=None
    ):
        parts.append(
            dict(
                id=pid,
                name=name,
                origin_mm=origin,
                size_mm=size,
                panel_axes=axes,
                material=material,
                group=group,
                bands_mm=bands or dict(u0=0, u1=0, v0=0, v1=0),
                grain="none",
                allow_rotation=True,
            )
        )

    part("SIDE_L", "Лява страница", [0, carcass_y, 100], [18, cd, 2100], [1, 2])
    part("SIDE_R", "Дясна страница", [1182, carcass_y, 100], [18, cd, 2100], [1, 2])
    part("BOTTOM", "Дъно", [18, carcass_y, 100], [1164, cd, 18], [0, 1])
    part("TOP", "Таван", [18, carcass_y, 2182], [1164, cd, 18], [0, 1])
    part("DIVIDER", "Средна преграда", [591, carcass_y, 118], [18, cd, 2064], [1, 2])
    part(
        "DRAWER_TOP",
        "Плот над чекмеджетата",
        [left_x, carcass_y, 500],
        [clear, cd, 18],
        [0, 1],
        group="shelf",
    )
    # Four equal CLEAR openings between platform and underside of top panel.
    clear_left = (2182 - 518 - 3 * T) / 4
    for i in range(3):
        z = 518 + clear_left * (i + 1) + T * i
        part(
            f"SHELF_L{i+1}",
            f"Ляв рафт {i+1}",
            [left_x, 30, z],
            [clear, 557, T],
            [0, 1],
            group="shelf",
        )
    # Exactly 1100 clear above upper shelf. Two equal lower clear openings.
    upper_z = 2182 - 1100 - T
    clear_right = (upper_z - 118 - T) / 2
    part(
        "SHELF_R1",
        "Десен долен рафт",
        [right_x, 30, 118 + clear_right],
        [clear, 557, T],
        [0, 1],
        group="shelf",
    )
    part(
        "SHELF_R2",
        "Десен горен рафт",
        [right_x, 30, upper_z],
        [clear, 557, T],
        [0, 1],
        group="shelf",
    )
    # 2-mm design gaps; the 1700/200/200 bands are nominal, not raw cut dimensions.
    band = dict(u0=1, u1=1, v0=1, v1=1)
    part(
        "DOOR_L",
        "Лява врата",
        [2, front_y, 502],
        [597, 18, 1696],
        [0, 2],
        "cream",
        "front",
        band.copy(),
    )
    part(
        "DOOR_R",
        "Дясна врата",
        [601, front_y, 102],
        [597, 18, 2096],
        [0, 2],
        "cream",
        "front",
        band.copy(),
    )
    for i, z in enumerate([102, 302], 1):
        part(
            f"FRONT_D{i}",
            f"Чело чекмедже {i}",
            [2, front_y, z],
            [597, 18, 198],
            [0, 2],
            "cream",
            "front",
            band.copy(),
        )
        # Provisional wooden drawer box: 13 mm slide allowance per side; no drilling.
        base = 138 + (i - 1) * 200
        x = 31
        y = 40
        bw = 547
        depth = 500
        wall_h = 140
        part(
            f"D{i}_SIDE_L",
            f"Чекмедже {i} — лява страна",
            [x, y, base + 3],
            [18, depth, wall_h],
            [1, 2],
            group="drawer",
        )
        part(
            f"D{i}_SIDE_R",
            f"Чекмедже {i} — дясна страна",
            [x + bw - 18, y, base + 3],
            [18, depth, wall_h],
            [1, 2],
            group="drawer",
        )
        part(
            f"D{i}_INNER_F",
            f"Чекмедже {i} — предна стена",
            [x + 18, y, base + 3],
            [bw - 36, 18, wall_h],
            [0, 2],
            group="drawer",
        )
        part(
            f"D{i}_INNER_B",
            f"Чекмедже {i} — задна стена",
            [x + 18, y + depth - 18, base + 3],
            [bw - 36, 18, wall_h],
            [0, 2],
            group="drawer",
        )
        part(
            f"D{i}_BOTTOM",
            f"Чекмедже {i} — дъно",
            [x, y, base],
            [bw, depth, 3],
            [0, 1],
            "hdf",
            "drawer",
        )
    part("BACK", "Гръб HDF", [0, back_y, 100], [W, 3, 2100], [0, 2], "hdf", "back")
    part(
        "PLINTH_F", "Преден цокъл", [18, 70, 0], [1164, 18, 100], [0, 2], group="plinth"
    )
    part(
        "PLINTH_B",
        "Задна цокълна опора",
        [18, 540, 0],
        [1164, 18, 100],
        [0, 2],
        group="plinth",
    )
    fittings = [
        dict(
            id="RAIL",
            name="Лост за дрехи — условна позиция",
            origin_mm=[609, 295, 2080],
            size_mm=[573, 25, 25],
            shape="cylinder",
            axis=0,
            color="#a5adb1",
            group="hardware",
        )
    ]
    for pid, x, z in [("HANDLE_L", 562, 1280), ("HANDLE_R", 630, 1280)]:
        fittings.append(
            dict(
                id=pid,
                name="Дръжка — условен модел",
                origin_mm=[x, -22, z],
                size_mm=[9, 22, 128],
                color="#69767d",
                group="hardware",
                hide_with_fronts=True,
            )
        )
    for i, z in enumerate([195, 395], 1):
        fittings.append(
            dict(
                id=f"HANDLE_D{i}",
                name="Дръжка чекмедже — условен модел",
                origin_mm=[235, -22, z],
                size_mm=[128, 22, 9],
                color="#69767d",
                group="hardware",
                hide_with_fronts=True,
            )
        )
    return dict(
        schema_version=1,
        units="mm",
        name="Гардероб с две чекмеджета",
        subtitle="По схемата на клиента · 1200 × 2200 × 600 mm · Предварителна версия",
        source_image="source.jpeg",
        design_bounds_mm=dict(min=[0, 0, 0], max=[W, D, H]),
        pricing=dict(
            as_of_date="2026-11-20",
            max_price_age_days=7,
            material_scope_complete=False,
            dimension_annotations=[dict(id="hanging-clear", label="Светло за закачалки", start_part="SHELF_R2", start_face="max", end_part="TOP", end_face="min", axis=2)],
        materials={
                "white": dict(product_id="white-p0-18", confirmed=False),
                "cream": dict(product_id="agt-730a-18", confirmed=True),
            },
            edges={},
            hardware=[
                dict(
                    label="Водачи 500 mm — два комплекта",
                    quantity=2,
                    unit="pair",
                    product_id="slide-500-h35",
                    confirmed=False,
                    note="Примерен бюджетен модел; съвместимостта с кутиите не е потвърдена.",
                ),
                dict(
                    label="Панти за двете врати",
                    quantity=None,
                    unit="piece",
                    product_id="hinge-110-soft",
                    confirmed=False,
                    note="Броят и монтажните пластини се определят по тегло и каталог на производителя.",
                ),
                dict(label="Дръжки", quantity=4, unit="piece", confirmed=False),
                dict(label="Лост и държачи", quantity=1, unit="set", confirmed=False),
                dict(
                    label="Крепежи, рафтоносачи, лепило и консумативи",
                    quantity=None,
                    unit="set",
                    confirmed=False,
                ),
                dict(
                    label="Кант на корпуса, рафтовете и цокъла",
                    quantity=None,
                    unit="m",
                    confirmed=False,
                ),
            ],
        ),
        dimension_annotations=[dict(id="hanging-clear", label="Светло за закачалки", start_part="SHELF_R2", start_face="max", end_part="TOP", end_face="min", axis=2)],
        materials={
            "white": dict(
                name="Бяло ПДЧ",
                kind="particleboard",
                thickness_mm=18,
                color="#f0f0ec",
                finish_note="Приблизителен бял мат; без мостра",
                stock=dict(
                    x_mm=2800, y_mm=2070, trim_mm=20, kerf_mm=4, primary_axis="Y"
                ),
            ),
            "cream": dict(
                name="MDF AGT 730A — крем мат",
                kind="mdf",
                thickness_mm=18,
                color="#e2e0d1",
                color_source=json.loads((ROOT / "references/material-sources.json").read_text())["agt-730"],
                finish_note="Цвят от официалната цифрова мостра AGT 730 Soft Touch Cream; артикулът на ROSI е 730A. Екранен ориентир, не измерен физически цвят.",
                stock=dict(
                    x_mm=2800, y_mm=1220, trim_mm=20, kerf_mm=4, primary_axis="Y"
                ),
            ),
            "hdf": dict(
                name="Бял HDF",
                kind="hdf",
                thickness_mm=3,
                color="#e4e6e2",
                finish_note="Условен цвят; складов формат не е зададен",
                stock=None,
            ),
        },
        confirmed=[
            "Размери: ширина 1200 mm, височина 2200 mm, дълбочина 600 mm; единици mm.",
            "Две номинални секции по 600 mm. Светлата ширина е 573 mm при централна преграда 18 mm.",
            "Вертикална верига: 100 mm цокъл + 200 + 200 mm чекмеджета + 1700 mm горна зона = 2200 mm.",
            "Лява врата над две чекмеджета; дясна врата по височината над цокъла.",
            "Три леви рафта с равни светли разстояния; два долни десни рафта с равни светли разстояния.",
            "1100 mm е светлата височина от горната повърхност на десния горен рафт до долната повърхност на тавана; не височината на оста на лоста.",
            "Корпус: бяло ПДЧ 18 mm. Фронтове: кремав MDF AGT 730A, 18 mm. Гръб: бял HDF 3 mm.",
            "Кант на вратите 1 mm по четирите страни. Размерите за рязане са намалени спрямо крайните.",
            "ПДЧ 2800 × 2070 mm; MDF 2800 × 1220 mm. Последна ориентация: X=2800 mm; основни срезове успоредни на Y.",
        ],
        assumptions=[
            "Дълбочината 600 mm е използвана като общ габарит на плочите: фронт 18 + фуга 2 + корпус 577 + гръб 3 mm. Дръжките стърчат още 22 mm отпред. Това тълкуване трябва да се провери преди производство.",
            "Цокълът е затворен, съгласно писмения отговор „цокъл 100 mm“; символите под корпуса в скицата не определят конкретни крачета.",
            "Фугите са проектно приети: 2 mm от външните ръбове и 2 mm между фронтовете. Номиналните 1700/200 mm са зони, не крайни размери на фронтовете.",
            "Плотът над чекмеджетата е добавен на Z=500 mm; левите равни светли отвори са 402.5 mm. Нужен е конструктивен преглед.",
            "Кантовете на корпуса, рафтовете и цокъла не са потвърдени. Стойност 0 е временна за теста и не означава решение да останат некантирани.",
            "Кант 1 mm по четирите страни е приложен условно и към челата на чекмеджетата; изричното предходно потвърждение е за вратите.",
            "Окрайчване 20 mm на всяка страна и срез 4 mm са запазени от предишния проект; първоначално са въведени като допускания от асистента.",
            "Разрешено е завъртане; посоката на декора не е ограничена за този предварителен разкрой и изисква потвърждение.",
            "Кутиите на чекмеджетата са условни: ПДЧ 18 mm, дълбочина 500 mm, стени 140 mm, HDF дъно 3 mm, по 13 mm място за водач. Няма избран обков.",
            "HDF гърбът и дъната са в модела и CSV, но са изключени от разкроя, защото складовият формат на HDF не е зададен.",
            "Дръжките и лостът са условни модели и позиции. Пантите, водачите, отворите, крепежите и монтажът на гърба не са разработени.",
            "Кодът е коригиран от потребителя от AGT 780 на AGT 730A на 20.11.2026. Точната текстура на AGT 730A не е предоставена. Визуализацията използва приблизителни цветове.",
        ],
        parts=parts,
        fittings=fittings,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--source-image", type=Path)
    args = ap.parse_args()
    if args.out.exists():
        ap.error("Output already exists; choose a new filename")
    project = make_project()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.source_image:
        target = args.out.parent / "source.jpeg"
        if target.exists():
            ap.error("source.jpeg already exists")
        shutil.copyfile(args.source_image, target)
    args.out.write_text(json.dumps(project, ensure_ascii=False, indent=2))
    print(args.out)


if __name__ == "__main__":
    main()
