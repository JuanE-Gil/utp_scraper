"""Tests de la Fase 1 (cierre): matrícula agrupada por ciclo y carpetas sin colisión.

Los datos son sintéticos y reproducen la FORMA observada en fase1/fase1b_reporte.json:
6 tuplas (period, acadCareer, module), dos courseId repetidos entre secciones,
y un pseudo-período 9999 con dos módulos distintos.
"""

import os

from utp_scraper import api
from utp_scraper.core import DEFAULT_PERIOD, collect_jobs, group_courses_by_period


def course(name, period, career="PREG", module="001", section="s", course_id="c", cls="1", **extra):
    base = {
        "sectionId": section,
        "courseId": course_id,
        "name": name,
        "period": period,
        "acadCareer": career,
        "module": module,
        "classNumber": cls,
        "modality": "P",
        "sectionCode": f"{period}code{cls}",
        "teacherEmail": "docente@example.test",
        "teachers": [{"teacherEmail": "docente@example.test"}],
    }
    base.update(extra)
    return base


PERIODS = [
    {"period": "9999", "acadCareer": "PRED", "module": "000", "type": "CURRENT_PERIOD", "name": "Período Predeterminado"},
    {"period": "2252", "acadCareer": "PREG", "module": "001", "type": "OLD_PERIOD", "name": "2025 - Ciclo 1 Marzo PREG (001)"},
    {"period": "2262", "acadCareer": "PREG", "module": "001", "type": "OLD_PERIOD", "name": "2026 - Ciclo 1 Marzo PREG (001)"},
    {"period": "2253", "acadCareer": "PREG", "module": "001", "type": "OLD_PERIOD", "name": "2025 - Ciclo 2 Agosto PREG (001)"},
    {"period": "9999", "acadCareer": "PRED", "module": "011", "type": "OLD_PERIOD", "name": "PRED-MARZO25  (011)"},
    {"period": "2263", "acadCareer": "PREG", "module": "001", "type": "CURRENT_PERIOD", "name": "2026 - Ciclo 2 Agosto PREG (001)"},
]


def fixture_courses():
    return [
        course("Transversal A", "9999", "PRED", "000", section="s-t1", course_id="c-t1"),
        course("Ruta Laboral", "9999", "PRED", "011", section="s-r0", course_id="c-ruta"),
        course("Mecánica", "2263", section="s-m", course_id="c-mec"),
        course("Ruta Laboral", "2263", section="s-r1", course_id="c-ruta"),
        course("Matemática II", "2262", section="s-ma2", course_id="c-mat2"),
        course("Ruta Laboral", "2262", section="s-r2", course_id="c-ruta"),
        course("Matemática II", "2253", section="s-ma1", course_id="c-mat2"),
        course("Inglés I", "2252", section="s-i", course_id="c-ing"),
    ]


def test_groups_are_keyed_by_period_career_module_not_period_alone():
    groups, excluded = group_courses_by_period(fixture_courses(), PERIODS)
    assert excluded == []
    keys = [g["key"] for g in groups]
    assert len(keys) == 6
    assert ("9999", "PRED", "000") in keys and ("9999", "PRED", "011") in keys


def test_order_current_first_then_older_desc_then_default_last():
    groups, _ = group_courses_by_period(fixture_courses(), PERIODS)
    assert [g["key"][0] for g in groups] == ["2263", "2262", "2253", "2252", "9999", "9999"]
    assert groups[0]["is_current"] is True
    assert all(g["is_current"] is False for g in groups[1:])
    assert [g["is_default"] for g in groups] == [False] * 4 + [True, True]


def test_default_period_is_never_current_even_if_typed_current():
    groups, _ = group_courses_by_period(fixture_courses(), PERIODS)
    default_000 = next(g for g in groups if g["key"] == ("9999", "PRED", "000"))
    assert default_000["is_current"] is False
    assert DEFAULT_PERIOD == "9999"


def test_labels_come_from_academic_periods_and_fall_back_without_them():
    groups, _ = group_courses_by_period(fixture_courses(), PERIODS)
    assert groups[0]["label"] == "2026 - Ciclo 2 Agosto PREG (001)"
    groups_nometa, _ = group_courses_by_period(fixture_courses(), None)
    assert groups_nometa[0]["label"] == "Ciclo 2263 (001)"


def test_without_periods_the_highest_regular_code_is_flagged_current():
    groups, _ = group_courses_by_period(fixture_courses(), None)
    assert [g["is_current"] for g in groups] == [True, False, False, False, False, False]


def test_folders_never_collide_for_repeated_courses_across_periods():
    groups, _ = group_courses_by_period(fixture_courses(), PERIODS)
    folders = [c["folder"] for g in groups for c in g["courses"]]
    assert len(folders) == len(set(folders)) == 8
    ruta = [c["folder"] for g in groups for c in g["courses"] if c["name"] == "Ruta Laboral"]
    assert len(ruta) == 3 and len(set(ruta)) == 3


def test_same_name_in_same_period_gets_class_number_suffix():
    cs = [
        course("Taller", "2263", section="a", course_id="c1", cls="111"),
        course("Taller", "2263", section="b", course_id="c2", cls="222"),
    ]
    groups, _ = group_courses_by_period(cs, PERIODS)
    folders = [c["folder"] for c in groups[0]["courses"]]
    assert len(set(folders)) == 2
    assert any("111" in f for f in folders) and any("222" in f for f in folders)


def test_courses_without_section_id_are_excluded_no_alias_fallback():
    bad = course("Sin sección", "2263", section="", course_id="c-x")
    alias_only = course("Solo alias", "2263", section="", course_id="c-y")
    alias_only.pop("sectionId")  # tiene sectionCode, pero ADR-0005: NO se usa como sustituto
    groups, excluded = group_courses_by_period([bad, alias_only] + fixture_courses(), PERIODS)
    assert len(excluded) == 2
    assert sum(len(g["courses"]) for g in groups) == 8


def test_normalized_record_does_not_carry_teacher_data():
    groups, _ = group_courses_by_period(fixture_courses(), PERIODS)
    rec = groups[0]["courses"][0]
    assert set(rec) == {"section_id", "course_id", "name", "class_number", "modality", "period", "folder"}
    assert "docente@example.test" not in repr(groups)


def test_collect_jobs_default_folder_unchanged_and_override_works():
    data = {
        "unities": [
            {"themes": [{"weekNumber": 1, "name": "Tema", "contents": [
                {"type": "FILE", "title": "t", "metadata": {"url": "https://x/y.pdf", "filetype": "pdf"}}
            ]}]}
        ]
    }
    default_jobs = collect_jobs(data, "Mecánica Clásica")
    assert default_jobs[0][2] == os.path.join("Mecanica Clasica", "Semana_01", "Tema")
    custom = collect_jobs(data, "Mecánica Clásica", folder=os.path.join("Ciclo", "Mecanica"))
    assert custom[0][2] == os.path.join("Ciclo", "Mecanica", "Semana_01", "Tema")


class _FakeResp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


def test_api_list_dashboard_courses_uses_user_scoped_url(monkeypatch):
    seen = {}

    def fake_get(url, headers=None, timeout=None):
        seen["url"] = url
        return _FakeResp({"data": [{"sectionId": "s"}]})

    monkeypatch.setattr(api.requests, "get", fake_get)
    out = api.list_dashboard_courses("USER", {"h": 1})
    assert seen["url"] == "https://api-pao.utpxpedition.com/learning/student/USER/dashboard-courses"
    assert out == [{"sectionId": "s"}]


def test_api_list_academic_periods_unwraps_nested_list(monkeypatch):
    seen = {}

    def fake_get(url, headers=None, timeout=None):
        seen["url"] = url
        return _FakeResp({"data": {"academicPeriods": [{"period": "2263"}]}})

    monkeypatch.setattr(api.requests, "get", fake_get)
    assert api.list_academic_periods("USER", {}) == [{"period": "2263"}]
    assert seen["url"] == "https://api-pao.utpxpedition.com/course/student/USER/academicperiods"