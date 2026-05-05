"""CSES.today_schedule 单元测试。"""
import datetime

import pytest

import cses
from cses import errors
from cses.structures.v1 import (
    Lesson as V1Lesson,
    SingleDaySchedule as V1SingleDaySchedule,
)
from cses.structures.v2 import (
    Configuration,
    CycleConfig,
    CycleSpan,
    Lesson as V2Lesson,
    SingleDaySchedule as V2SingleDaySchedule,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_v1_cses(schedules: list[V1SingleDaySchedule]) -> cses.CSES:
    """构造一个 version=1 的 CSES 对象（绕过 YAML 解析）。"""
    obj = cses.CSES.__new__(cses.CSES)
    obj.version = 1
    obj.subjects = []
    obj.schedules = schedules
    obj.configuration = None
    obj._cses = None  # _gen_dict 不会被调用，置 None 即可
    return obj


def _build_v2_cses(
    schedules: list[V2SingleDaySchedule],
    work_count: int = 10,
    rest_count: int = 4,
) -> cses.CSES:
    """构造一个 version=2 的 CSES 对象。"""
    obj = cses.CSES.__new__(cses.CSES)
    obj.version = 2
    obj.subjects = []
    obj.schedules = schedules
    obj.configuration = Configuration(
        name='test',
        cycle=CycleConfig(
            work_count=work_count,
            rest_count=rest_count,
            spans=(
                CycleSpan(activity='work', count=work_count),
                CycleSpan(activity='rest', count=rest_count),
            ),
        ),
    )
    obj._cses = None
    return obj


# ---------------------------------------------------------------------------
# V1 Tests
# ---------------------------------------------------------------------------


class TestV1TodaySchedule:
    """version=1 的 today_schedule 测试。"""

    # -- 基本匹配 --

    def test_weeks_all_matches_weekday(self):
        """weeks='all' 时，匹配对应星期的 schedule。"""
        schedule_all = V1SingleDaySchedule(
            enable_day=1,
            classes=[
                V1Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期一',
            weeks='all',
        )
        cses_obj = _build_v1_cses([schedule_all])

        # 2026-05-04 是星期一
        result = cses_obj.today_schedule(
            start_day=datetime.date(2026, 5, 1),
            day=datetime.date(2026, 5, 4),
        )
        assert result is schedule_all

    def test_weeks_all_returns_first_matching_weekday(self):
        """同一星期存在多个 schedule 时，weeks='all' 优先返回。"""
        schedule_all = V1SingleDaySchedule(
            enable_day=2,
            classes=[
                V1Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期二-全周',
            weeks='all',
        )
        schedule_odd = V1SingleDaySchedule(
            enable_day=2,
            classes=[
                V1Lesson(
                    subject='物理', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期二-单周',
            weeks='odd',
        )
        cses_obj = _build_v1_cses([schedule_all, schedule_odd])

        # 2026-05-05 是星期二
        result = cses_obj.today_schedule(
            start_day=datetime.date(2026, 5, 1),
            day=datetime.date(2026, 5, 5),
        )
        assert result is schedule_all

    # -- 奇偶周 --

    def test_odd_week_matches(self):
        """单周日期应匹配 weeks='odd' 的 schedule。"""
        schedule_odd = V1SingleDaySchedule(
            enable_day=2,
            classes=[
                V1Lesson(
                    subject='物理', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期二-单周',
            weeks='odd',
        )
        schedule_even = V1SingleDaySchedule(
            enable_day=2,
            classes=[
                V1Lesson(
                    subject='英语', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期二-双周',
            weeks='even',
        )
        cses_obj = _build_v1_cses([schedule_odd, schedule_even])

        # start_day=2026-05-01(Fri), day=2026-05-05(Tue) => week_num = (4//7)+1 = 1 (奇数)
        result = cses_obj.today_schedule(
            start_day=datetime.date(2026, 5, 1),
            day=datetime.date(2026, 5, 5),
        )
        assert result is schedule_odd

    def test_even_week_matches(self):
        """双周日期应匹配 weeks='even' 的 schedule。"""
        schedule_odd = V1SingleDaySchedule(
            enable_day=2,
            classes=[
                V1Lesson(
                    subject='物理', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期二-单周',
            weeks='odd',
        )
        schedule_even = V1SingleDaySchedule(
            enable_day=2,
            classes=[
                V1Lesson(
                    subject='英语', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期二-双周',
            weeks='even',
        )
        cses_obj = _build_v1_cses([schedule_odd, schedule_even])

        # start_day=2026-05-01(Fri), day=2026-05-12(Tue) => week_num = (11//7)+1 = 2 (偶数)
        result = cses_obj.today_schedule(
            start_day=datetime.date(2026, 5, 1),
            day=datetime.date(2026, 5, 12),
        )
        assert result is schedule_even

    # -- 无匹配 --

    def test_no_matching_weekday_raises(self):
        """没有匹配星期的 schedule 时应抛出 CSESError。"""
        schedule_mon = V1SingleDaySchedule(
            enable_day=1,
            classes=[
                V1Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期一',
            weeks='all',
        )
        cses_obj = _build_v1_cses([schedule_mon])

        # 2026-05-05 是星期二，没有对应 schedule
        with pytest.raises(errors.CSESError, match='未找到'):
            cses_obj.today_schedule(
                start_day=datetime.date(2026, 5, 1),
                day=datetime.date(2026, 5, 5),
            )

    def test_weekday_matches_but_week_type_mismatches_raises(self):
        """星期匹配但周次不匹配时，应继续查找并最终抛出 CSESError。"""
        schedule_odd = V1SingleDaySchedule(
            enable_day=2,
            classes=[
                V1Lesson(
                    subject='物理', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='星期二-单周',
            weeks='odd',
        )
        cses_obj = _build_v1_cses([schedule_odd])

        # start_day=2026-05-01, day=2026-05-12(Tue) => week_num=2 (偶数)，不匹配 odd
        with pytest.raises(errors.CSESError, match='未找到'):
            cses_obj.today_schedule(
                start_day=datetime.date(2026, 5, 1),
                day=datetime.date(2026, 5, 12),
            )

    # -- day 默认值 --

    def test_default_day_uses_today(self):
        """day=None 时应使用 datetime.date.today()。"""
        schedule_all = V1SingleDaySchedule(
            enable_day=datetime.date.today().weekday() + 1,
            classes=[
                V1Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='今天',
            weeks='all',
        )
        cses_obj = _build_v1_cses([schedule_all])

        result = cses_obj.today_schedule(start_day=datetime.date.today())
        assert result is schedule_all


# ---------------------------------------------------------------------------
# V2 Tests
# ---------------------------------------------------------------------------


class TestV2TodaySchedule:
    """version=2 的 today_schedule 测试。"""

    def test_basic_cycle_match(self):
        """基本周期匹配：day - start_day 偏移量在 enable_day 中。"""
        schedule = V2SingleDaySchedule(
            enable_day=(1, 2, 3),
            classes=[
                V2Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='工作日',
        )
        cses_obj = _build_v2_cses([schedule], work_count=5, rest_count=2)

        # (day - start_day).days + 1 = 1 => 1 % 7 = 1, 在 (1,2,3) 中
        result = cses_obj.today_schedule(
            start_day=datetime.date(2026, 5, 1),
            day=datetime.date(2026, 5, 1),
        )
        assert result is schedule

    def test_cycle_wraps_around(self):
        """周期应正确循环：偏移量超过 work+rest 后取模。"""
        schedule_a = V2SingleDaySchedule(
            enable_day=(1,),
            classes=[
                V2Lesson(
                    subject='A', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='A日',
        )
        schedule_b = V2SingleDaySchedule(
            enable_day=(2,),
            classes=[
                V2Lesson(
                    subject='B', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='B日',
        )
        cses_obj = _build_v2_cses(
            [schedule_a, schedule_b], work_count=5, rest_count=2
        )

        # 周期长度 = 5+2 = 7
        # day=2026-05-08 => (7)+1 = 8 => 8 % 7 = 1 => 匹配 schedule_a
        result = cses_obj.today_schedule(
            start_day=datetime.date(2026, 5, 1),
            day=datetime.date(2026, 5, 8),
        )
        assert result is schedule_a

    def test_rest_day_in_cycle(self):
        """周期中的休息日（enable_day 不含该数字）应抛出 CSESError。"""
        schedule = V2SingleDaySchedule(
            enable_day=(1, 2, 3, 4, 5),
            classes=[
                V2Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='工作日',
        )
        cses_obj = _build_v2_cses([schedule], work_count=5, rest_count=2)

        # day=2026-05-06 => (5)+1 = 6 => 6 % 7 = 6，不在 (1,2,3,4,5) 中
        with pytest.raises(errors.CSESError, match='未找到'):
            cses_obj.today_schedule(
                start_day=datetime.date(2026, 5, 1),
                day=datetime.date(2026, 5, 6),
            )

    def test_no_schedule_for_day_raises(self):
        """没有任何 schedule 匹配时应抛出 CSESError。"""
        schedule = V2SingleDaySchedule(
            enable_day=(99,),
            classes=[
                V2Lesson(
                    subject='X', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='不存在',
        )
        cses_obj = _build_v2_cses([schedule], work_count=5, rest_count=2)

        with pytest.raises(errors.CSESError, match='未找到'):
            cses_obj.today_schedule(
                start_day=datetime.date(2026, 5, 1),
                day=datetime.date(2026, 5, 1),
            )

    def test_multiple_enable_days(self):
        """enable_day 包含多个值时，匹配任意一个即可。"""
        schedule = V2SingleDaySchedule(
            enable_day=(1, 5, 10),
            classes=[
                V2Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='多日',
        )
        cses_obj = _build_v2_cses([schedule], work_count=10, rest_count=4)

        # day=2026-05-05 => (4)+1 = 5 => 5 % 14 = 5，在 (1,5,10) 中
        result = cses_obj.today_schedule(
            start_day=datetime.date(2026, 5, 1),
            day=datetime.date(2026, 5, 5),
        )
        assert result is schedule

    def test_default_day_uses_today_v2(self):
        """day=None 时应使用 datetime.date.today()（v2）。"""
        today_offset = (
            datetime.date.today() - datetime.date(2026, 1, 1)
        ).days + 1
        today_num = today_offset % 14  # work=10, rest=4

        schedule = V2SingleDaySchedule(
            enable_day=(today_num,),
            classes=[
                V2Lesson(
                    subject='数学', start_time='08:00:00', end_time='09:00:00'
                )
            ],
            name='今天',
        )
        cses_obj = _build_v2_cses([schedule], work_count=10, rest_count=4)

        result = cses_obj.today_schedule(start_day=datetime.date(2026, 1, 1))
        assert result is schedule


# ---------------------------------------------------------------------------
# Version Dispatch Tests
# ---------------------------------------------------------------------------


class TestVersionDispatch:
    """today_schedule 版本分发测试。"""

    def test_unsupported_version_raises(self):
        """version 不是 1 或 2 时应抛出 VersionError。"""
        obj = cses.CSES.__new__(cses.CSES)
        obj.version = 99
        obj.subjects = []
        obj.schedules = []
        obj.configuration = None
        obj._cses = None

        with pytest.raises(errors.VersionError, match='不支持的版本'):
            obj.today_schedule(
                start_day=datetime.date(2026, 5, 1),
                day=datetime.date(2026, 5, 1),
            )
