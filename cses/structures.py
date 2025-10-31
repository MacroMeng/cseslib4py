"""
本文档是cses包中的structures.py文件的文档。
该文件定义了课程相关的数据结构，包括科目、课程、周次类型和单日课程安排。

.. caution:: 该模块中的数据结构仅用于表示课程结构（与其附属工具），不包含实际的读取/写入功能。
"""
import datetime
from collections import UserList
from collections.abc import Sequence
from typing import override, Optional, Literal, Annotated

from pydantic import BaseModel, ValidationError, BeforeValidator, field_serializer

import cses.utils as utils


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
        start_time (str | int | datetime.time): 开始的时间（若输入为 ``str`` 或 ``int`` ，则会转化为datetime.time对象）
        end_time (str | int | datetime.time): 结束的时间（若输入为 ``str`` 或 ``int`` ，则会转化为datetime.time对象）

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
        enable_day (int): 课程安排的星期（如 1 表示星期一）
        classes (list[Lesson]): 课程列表，每个课程包含科目、开始时间和结束时间
        name (str): 课程安排名称（如 "星期一"）
        weeks (WeekType): 周次类型，指定课程适用于哪些周次

    Examples:
        >>> s = SingleDaySchedule(enable_day=1, classes=[Lesson(subject=Subject(name='语文', \
                                  simplified_name='语', teacher='张三'), start_time=datetime.time(8, 0, 0), \
                                  end_time=datetime.time(8, 45, 0))], name='星期一', weeks='all')
        >>> s.enable_day
        1
        >>> s.name
        '星期一'
        >>> s.weeks
        'all'
    """
    enable_day: Literal[1, 2, 3, 4, 5, 6, 7]
    classes: list[Lesson]
    name: str
    weeks: Literal['all', 'odd', 'even']

    def is_enabled_on_week(self, week: int) -> bool:
        """
        判断课程是否在指定的日期上启用。

        Args:
            week (int): 要检查的周次序号

        Returns:
            bool: 如果课程在指定周上启用，则返回 True；否则返回 False

        Examples:
            >>> s = SingleDaySchedule(enable_day=1, classes=[Lesson(subject=Subject(name='语文', \
                                      simplified_name='语', teacher='张三'), start_time=datetime.time(8, 0, 0), \
                                      end_time=datetime.time(8, 45, 0))], name='星期一', weeks='odd')
            >>> s.is_enabled_on_week(3)
            True
            >>> s.is_enabled_on_week(6)
            False
            >>> s.is_enabled_on_week(11)
            True
        """
        return {
            'all': True,  # 适用于所有周 -> 永久启用
            'odd': week % 2 == 1,  # 单周
            'even': week % 2 == 0  # 双周
        }[self.weeks]

    def is_enabled_on_day(self, start_day: datetime.date, day: datetime.date) -> bool:
        """
        判断课程是否在指定的日期上启用。

        Args:
            day (int): 要检查的日期（1 表示星期一，2 表示星期二，依此类推）
            start_day (datetime.date): 课程开始的日期，用于计算周次

        Returns:
            bool: 如果课程在指定日期上启用，则返回 True；否则返回 False

        Examples:
            >>> s = SingleDaySchedule(enable_day=1, classes=[Lesson(subject=Subject(name='语文', \
                                      simplified_name='语', teacher='张三'), start_time=datetime.time(8, 0, 0), \
                                      end_time=datetime.time(8, 45, 0))], name='星期一', weeks='odd')
            >>> s.is_enabled_on_day(datetime.date(2025, 9, 1), datetime.date(2025, 9, 4))
            True
            >>> s.is_enabled_on_day(datetime.date(2025, 9, 1), datetime.date(2025, 9, 16))
            True
            >>> s.is_enabled_on_day(datetime.date(2025, 9, 1), datetime.date(2025, 9, 24))
            False
        """
        return self.is_enabled_on_week(utils.week_num(start_day, day))


class Schedule(UserList[SingleDaySchedule]):
    """
    存储每天课程安排的列表。列表会按照星期排序。

    .. caution::
        在访问一个 ``Schedule`` 中的项目时，注意索引从 1 开始，而不是从 0 开始。
        这是为了可以按照星期访问课表，而不是按照 Python 的逻辑，所以访问星期一的课表使用 ``schedule[1]`` 而不是 ``schedule[0]`` 。
        若你想要以 Python 的逻辑访问课表，请使用 ``data`` 属性，如访问星期一的课表需要使用 ``schedule.data[0]`` 。

    Examples:
        >>> s = Schedule([
        ...     SingleDaySchedule(enable_day=1, classes=[Lesson(subject=Subject(name='语文',
        ...                       simplified_name='语', teacher='张三'), start_time=datetime.time(8, 0, 0),
        ...                       end_time=datetime.time(8, 45, 0))], name='星期一', weeks='odd'),
        ...     SingleDaySchedule(enable_day=2, classes=[Lesson(subject=Subject(name='数学',
        ...                       simplified_name='数', teacher='李四'), start_time=datetime.time(9, 0, 0),
        ...                       end_time=datetime.time(9, 45, 0))], name='星期二', weeks='even')
        ... ])
        >>> s[1].enable_day
        1
    """
    def __init__(self, args: Sequence[SingleDaySchedule]):
        result = sorted(args, key=lambda arg: arg.enable_day)  # 按照启用日期（星期几）排序
        super().__init__(result)

    @override
    def __getitem__(self, index: int) -> SingleDaySchedule:
        return self.data[index]
