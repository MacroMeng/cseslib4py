"""使用 ``CSES`` 类可以表示、解析一个 CSES 课程文件。"""
import datetime
import os
from typing import MutableSequence, cast

import yaml  # type: ignore [import]

import cses.structures as st
import cses.errors as err
from cses.structures.v2 import SingleDaySchedule
from cses.utils import log, repr_, SupportsRead, SupportsWrite
from cses import utils

yaml.add_representer(datetime.time, utils.serialize_time)
log.info('cseslib4py initialized!')


class CSES:
    """
    用来表示、解析一个 CSES 课程文件的类。

    该类有如下属性：
        - ``schedules``: 课程安排列表，每个元素是一个 ``SingleDaySchedule`` 对象。
        - ``version``: 课程文件的版本号。目前只能为 ``1`` ，参见 CSES 官方文档与 Schema 文件。
        - ``subjects``: 科目列表，每个元素是一个 ``Subject`` 对象。
        - ``configuration``: 课程配置，仅在 ``version`` 为 ``2`` 时不为 ``None``。

    Examples:
        >>> c1 = CSES.load_from('../examples/cses_example.yaml')
        >>> c1.version
        1
        >>> c1.subjects  # doctest: +NORMALIZE_WHITESPACE
        [Subject(name='数学', simplified_name='数', teacher='李梅', room='101'),
         Subject(name='语文', simplified_name='语', teacher='王芳', room='102'),
         Subject(name='英语', simplified_name='英', teacher='张伟', room='103'),
         Subject(name='物理', simplified_name='物', teacher='赵军', room='104')]
        >>> c2 = CSES.load_from('../examples/cses_example_v2.yaml')
        >>> c2.version
        2
        >>> c2.subjects  # doctest: +NORMALIZE_WHITESPACE
        [Subject(name='数学', simplified_name='数', teacher='李梅', location='101'),
         Subject(name='语文', simplified_name='语', teacher='王芳', location='102'),
         Subject(name='英语', simplified_name='英', teacher='张伟', location='103'),
         Subject(name='物理', simplified_name='物', teacher='赵军', location='104')]

    """

    def __init__(self):
        """
        初始化一个空CSES课表。

        .. warning:: 不应该直接调用 ``CSES()`` 构造函数， 而是应该使用 ``CSES.from_str()`` 工厂方法。
        """
        self._cses: st.v1.CSESStructV1 | st.v2.CSESStructV2 | None = None
        self.version = -1
        self.subjects: MutableSequence = []
        self.schedules: MutableSequence = []
        self.configuration: st.v2.Configuration | None = None

    def today_schedule(
        self, start_day: datetime.date, day: datetime.date | None = None
    ) -> 'SingleDaySchedule':
        """
        获取当前日期/指定日期的课程安排。

        Args:
            start_day (datetime.date): 课程开始的日期，用于计算周次。
            day (datetime.date, optional): 要获取的日期，默认是当前日期。

        Returns:
            SingleDaySchedule: 当前日期/指定日期的课程安排。

        Raises:
            CSESError: 如果在指定日期没有找到对应的课程安排。
        """
        if day is None:
            day = datetime.date.today()

        if self.version == 1:
            return self._v1_today_schedule(start_day, day)
        elif self.version == 2:
            return self._v2_today_schedule(start_day, day)
        else:
            raise err.VersionError(f'不支持的版本: {self.version}')

    @classmethod
    def loads(cls, content: str) -> 'CSES':
        """
        从 ``content`` 新建一个 CSES 课表对象。

        Args:
            content (str): CSES 课程文件的内容。
        """

        data = yaml.safe_load(content)
        new_schedule = cls()
        log.info(f'Loading CSES schedules {repr_(content)}')

        # 版本处理&检查
        log.debug(f"Checking version: {data['version']}")
        new_schedule.version = data['version']
        if new_schedule.version not in range(1, 2 + 1):
            raise err.VersionError(f'不支持的版本: {new_schedule.version}')

        used_module = st.v1 if new_schedule.version == 1 else st.v2
        used_cls = (
            st.v1.CSESStructV1
            if new_schedule.version == 1
            else st.v2.CSESStructV2
        )
        new_schedule._cses = used_cls(**data)
        new_schedule.subjects = new_schedule._cses.subjects
        # 直接使用 used_cls(**data) 会导致 new_schedule.schedules 为 list[dict[str, Any]] 类型，强制转换到 SingleDaySchedule 类型
        new_schedule.schedules = [
            used_module.SingleDaySchedule(
                **schedule  # ty: ignore [invalid-argument-type]
            )
            for schedule in new_schedule._cses.schedules
        ]
        if isinstance(new_schedule._cses, st.v2.CSESStructV2):
            new_schedule.configuration = new_schedule._cses.configuration

        log.info(f'Created Schedule: {repr_(new_schedule)}')
        return new_schedule

    @classmethod
    def load(cls, f: SupportsRead) -> 'CSES':
        """
        从文件对象 ``f`` 中读取并新建一个 CSES 课表对象。

        Args:
            f: 支持读取的文件对象。

        Returns:
            CSES: 新建的 CSES 课表对象。
        """
        return cls.loads(f.read())

    @classmethod
    def load_from(cls, fp: str) -> 'CSES':
        """
        从路径 ``fp`` 中读取并新建一个 CSES 课表对象。

        Args:
            fp (str): CSES 课程文件的路径。
        """
        with open(fp, encoding='utf8') as f:
            return CSES.loads(f.read())

    def dumps(self) -> str:
        """
        将当前 CSES 课表对象转换为 YAML 字符串。

        Returns:
            str: 当前 CSES 课表对象的 YAML 字符串表示。
        """
        res = yaml.dump(
            self._gen_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2,
            Dumper=utils.CustomizeDumper,
        )
        log.debug(f'Generated YAML: {repr_(res)}')
        return res

    def dump(self, fp: SupportsWrite) -> None:
        """
        将当前 CSES 课表对象存入指定的支持写入的对象。

        Args:
            fp: 支持写入的文件对象。
        """
        fp.write(self.dumps())

    def dump_to(self, fp: str, mode: str = 'w') -> None:
        """
        将当前 CSES 课表对象转换为 YAML CSES 课程CSES入路径 ``fp`` 中。若文件夹/文件不存在，则会自动创建。

        Args:
            fp (str): 要写入的文件路径。
            mode (str, optional): 写入模式，默认值为 ``'w'`` ，即覆盖写入。
        """
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, mode, encoding='utf8') as f:
            f.write(self.dumps())
        log.info(f'Written CSES schedule file to {repr_(fp)}.')

    def _gen_dict(self) -> dict:
        """
        生成当前 CSES 课表对象的字典表示。

        Returns:
            dict: 当前 CSES 课表对象的字典表示。
        """
        if self._cses is None:
            raise err.CSESError('未初始化 CSES 课表对象，无法生成字典表示。')
        return self._cses.model_dump()

    def _v1_today_schedule(
        self, start_day: datetime.date, day: datetime.date
    ) -> 'SingleDaySchedule':
        for schedule in self.schedules:
            if schedule.enable_day == day.weekday() + 1:
                # 相同的星期，判断周数
                if schedule.weeks == 'all':
                    return schedule  # 适用于所有周
                else:
                    if schedule.is_enabled_on_day(start_day, day):
                        return schedule
                    else:
                        continue
        else:
            raise err.CSESError(f'未找到 {day} 的课程安排。')

    def _v2_today_schedule(
        self, start_day: datetime.date, day: datetime.date
    ) -> 'SingleDaySchedule':
        cycle_config = cast(st.v2.Configuration, self.configuration).cycle

        today_num = (
            (day - start_day).days + 1
        ) % cycle_config.work_count + cycle_config.rest_count
        for schedule in self.schedules:
            if schedule.enable_day == today_num:
                return schedule
        else:
            raise err.CSESError(f'未找到 {day} 的课程安排。')

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._gen_dict() == other._gen_dict()
        else:
            return NotImplemented
