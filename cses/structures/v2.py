"""
本文档是 cses 包中 structures.py 文件的文档。此包只包括 CSES v2 数据结构。
该文件定义了课程相关的数据结构，包括科目、课程、周次类型和单日课程安排。

.. caution:: 该模块中的数据结构仅用于表示课程结构（与其附属工具），不包含实际的读取/写入功能。
"""
import datetime
from collections import UserList
from collections.abc import Sequence
from typing import Optional, Literal, Annotated  # pyright: ignore

from pydantic import BaseModel, BeforeValidator, field_serializer, field_validator

import cses.utils as utils
from cses.errors import ValidationError


class Subject(BaseModel):
    """
    单节课程科目。

    Args:
        name (str): 科目名称，如“语文”
        simplified_name (str): 科目简化名称，如“语”
        teacher (str): 教师姓名
        room (str): 教室名称

    Examples:
        >>> s = Subject(name='语文', simplified_name='语', teacher='张三', room='A101')
        >>> s.name
        '语文'
        >>> s.simplified_name
        '语'
        >>> s.teacher
        '张三'
        >>> s.room
        'A101'
    """
    name: str
    simplified_name: Optional[str] = None
    teacher: Optional[str] = None
    room: Optional[str] = None


class Lesson(BaseModel):
    """
    单节课程。

    Args:
        subject (str): 课程的科目，应与 ``Subject`` 中之一的 ``name`` 属性相同
        start_time (Union[str, int, datetime.time]): 开始的时间（若输入为 ``str`` 或 ``int`` ，则会转化为datetime.time对象）
        end_time (Union[str, int, datetime.time]): 结束的时间（若输入为 ``str`` 或 ``int`` ，则会转化为datetime.time对象）

    .. warning::
        ``start_time`` 与 ``end_time`` 均为 ``datetime.time`` 对象，即使输入为（合法的） ``str`` （针对时间文字） 或 ``int``  （针对一天中的秒数）。

    Examples:
        >>> l = Lesson(subject='语文', start_time="08:00:00", end_time="08:45:00")
        >>> l.subject
        '语文'
        >>> l.start_time
        datetime.time(8, 0)
        >>> l.end_time
        datetime.time(8, 45)
    """
    subject: str
    start_time: Annotated[datetime.time, BeforeValidator(utils.ensure_time)]
    end_time: Annotated[datetime.time, BeforeValidator(utils.ensure_time)]

    @field_serializer("start_time", "end_time")
    def serialize_time(self, time: datetime.time) -> str:
        return time.strftime("%H:%M:%S")


class SingleDaySchedule(BaseModel):
    """
    单日课程安排。

    Args:
        enable_day (tuple[int, ...]): 课程安排的星期（如 1 表示星期一）
        classes (list[Lesson]): 课程列表，每个课程包含科目、开始时间和结束时间
        name (str): 课程安排名称（如 "星期一"）

    Examples:
        >>> s = SingleDaySchedule(enable_day=(1, 8), classes=[Lesson(subject='语文', start_time=datetime.time(8, 0, 0), \
                                  end_time=datetime.time(8, 45, 0))], name='星期一')
        >>> s.enable_day
        (1, 8)
        >>> s.name
        '星期一'
    """
    enable_day: tuple[int, ...]
    classes: list[Lesson]
    name: str

    def is_enabled_on_week(self, week: int) -> bool:
        """
        判断课程是否在指定的周次上启用。

        Args:
            week (int): 要检查的周次序号

        Returns:
            bool: 如果课程在指定周上启用，则返回 True；否则返回 False

        Examples:
            >>> s = SingleDaySchedule(enable_day=(1, 8), classes=[Lesson(subject='语文', start_time=datetime.time(8, 0, 0), \
                                      end_time=datetime.time(8, 45, 0))], name='星期一')
            >>> s.is_enabled_on_week(3)
            True
            >>> s.is_enabled_on_week(6)
            False
            >>> s.is_enabled_on_week(11)
            True
        """
        raise NotImplementedError

    def is_enabled_on_day(self, start_day: datetime.date, day: datetime.date) -> bool:
        """
        判断课程是否在指定的日期上启用。

        Args:
            day (int): 要检查的日期（1 表示星期一，2 表示星期二，依此类推）
            start_day (datetime.date): 课程开始的日期，用于计算周次

        Returns:
            bool: 如果课程在指定日期上启用，则返回 True；否则返回 False

        Examples:
            >>> s = SingleDaySchedule(enable_day=(1, 8), classes=[Lesson(subject='语文', start_time=datetime.time(8, 0, 0), \
                                      end_time=datetime.time(8, 45, 0))], name='星期一')
            >>> s.is_enabled_on_day(datetime.date(2025, 9, 1), datetime.date(2025, 9, 4))
            True
            >>> s.is_enabled_on_day(datetime.date(2025, 9, 1), datetime.date(2025, 9, 16))
            True
            >>> s.is_enabled_on_day(datetime.date(2025, 9, 1), datetime.date(2025, 9, 24))
            False
        """
        raise NotImplementedError


class Schedule(UserList[SingleDaySchedule]):
    """
    存储每天课程安排的列表。列表会按照星期排序。

    .. caution::
        在访问一个 ``Schedule`` 中的项目时，注意索引从 0 开始。
        这意味着访问星期一的课表需要使用 ``schedule[0]`` ，而不是 ``schedule[1]`` 。

    Examples:
        >>> s = Schedule([
        ...     SingleDaySchedule(enable_day=(1, 8), classes=[Lesson(subject='语文', start_time=datetime.time(8, 0, 0),
        ...                       end_time=datetime.time(8, 45, 0))], name='星期一'),
        ...     SingleDaySchedule(enable_day=(2, 8), classes=[Lesson(subject='数学', start_time=datetime.time(9, 0, 0),
        ...                       end_time=datetime.time(9, 45, 0))], name='星期二')
        ... ])
        >>> s[0].enable_day
        (1, 8)
    """
    def __init__(self, args: Sequence[SingleDaySchedule]):
        result = sorted(args, key=lambda arg: arg.enable_day)  # 按照启用日期（星期几）排序
        super().__init__(result)


class CycleSpan(BaseModel):
    """
    课程周期的活动时间。

    Args:
        activity (Literal["work", "rest"]): 活动类型，"work" 表示上课，"rest" 表示休息
        count (int): 活动时间的天数（1-work_count 的整数）

    Examples:
        >>> s1 = CycleSpan(activity="work", count=3)  # 代表 5 天的上课时间
        >>> s2 = CycleSpan(activity="rest", count=2)  # 代表 2 天的休息时间
    """
    activity: Literal["work", "rest"]
    count: int  # 1-work_count 的整数

    @field_validator('count')
    @classmethod
    def validate_gt_1(cls, v: int) -> int:
        if v <= 1:
            raise ValidationError(f'count 必须 > 1，当前值为：{v}')
        else:
            return v


class CycleConfig(BaseModel):
    """
    课程周期的配置。

    Args:
        work_count (int): 大于 1 的整数，上课的总天数
        rest_count (int): 大于 1 的整数，休息的总天数
        spans (tuple[CycleSpan, ...]): 课程周期的活动时间配置，每个元素为一个 ``CycleSpan`` 实例

    若需按照以下列出的时间安排创建 ``CycleConfig`` 对象：

    - 上课 6 天，休息 1 天（代表一个小周）
    - 上课 5 天，休息 2 天（代表一个大周）

    则应使用如下的代码:
        >>> c = CycleConfig(work_count=11, rest_count=3,
                            spans=(CycleSpan(activity="work", count=6),
                                   CycleSpan(activity="rest", count=1),
                                   CycleSpan(activity="work", count=5),
                                   CycleSpan(activity="rest", count=2)))
    """
    work_count: int  # 大于 1 的整数，上课的总天数
    rest_count: int  # 大于 1 的整数，休息的总天数
    spans: tuple[CycleSpan, ...]

    @field_validator("work_count", "rest_count")
    @classmethod
    def validate_gt_1(cls, v: int) -> int:
        if v <= 1:
            raise ValidationError(f'work_count / rest_count 必须 > 1，当前值为：{v}')
        else:
            return v


class Configuration(BaseModel):
    name: str
    description: Optional[str]
    cycle: CycleConfig


class CSESStructV2(BaseModel):
    version: Literal[2]
    configuration: Configuration
    subjects: list[Subject]
    schedules: Schedule
