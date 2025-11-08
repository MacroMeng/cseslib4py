"""使用 ``CSES`` 类可以表示、解析一个 CSES 课程文件。"""
import datetime
import os

import pydantic
import yaml  # type: ignore [import]

import cses.structures as st
import cses.errors as err
from cses.utils import log, repr_
from cses import utils

yaml.add_representer(datetime.time, utils.serialize_time)
log.info("cseslib4py initialized!")


class CSES:
    """
    用来表示、解析一个 CSES 课程文件的类。

    该类有如下属性：
        - ``schedules``: 课程安排列表，每个元素是一个 ``SingleDaySchedule`` 对象。
        - ``version``: 课程文件的版本号。目前只能为 ``1`` ，参见 CSES 官方文档与 Schema 文件。
        - ``subjects``: 科目列表，每个元素是一个 ``Subject`` 对象。

    Examples:
        >>> c = CSES.from_file('../cses_example.yaml')
        >>> c.version  # 只会为 1
        1
        >>> c.subjects  # doctest: +NORMALIZE_WHITESPACE
        {'数学': Subject(name='数学', simplified_name='数', teacher='李梅', room='101'),
         '语文': Subject(name='语文', simplified_name='语', teacher='王芳', room='102'),
         '英语': Subject(name='英语', simplified_name='英', teacher='张伟', room='103'),
         '物理': Subject(name='物理', simplified_name='物', teacher='赵军', room='104')}

    """

    def __init__(self):
        """
        初始化一个空CSES课表。

        .. warning:: 不应该直接调用 ``CSES()`` 构造函数， 而是应该使用 ``CSES.from_str()`` 工厂方法。
        """
        self.version = 1
        self.subjects = {}
        self.schedules = st.Schedule([])

    @classmethod
    def from_str(cls, content: str) -> 'CSES':
        """
        从 ``content`` 新建一个 CSES 课表对象。

        Args:
            content (str): CSES 课程文件的内容。
        """

        data = yaml.safe_load(content)
        new_schedule = cls()
        log.info(f"Loading CSES schedules {repr_(content)}")

        # 版本处理&检查
        log.debug(f"Checking version: {data['version']}")
        new_schedule.version = data['version']
        if new_schedule.version != 1:
            raise err.VersionError(f'不支持的版本号: {new_schedule.version}')

        # 科目处理&检查
        try:
            log.debug(f"Processing subjects: {repr_(data['subjects'])}")
            new_schedule.subjects = {s['name']: st.Subject(**s) for s in data['subjects']}
        except pydantic.ValidationError as e:
            raise err.ParseError(f'科目数据有误: {data["subjects"]}') from e

        # 课程处理&检查
        schedules = data['schedules']
        log.debug(f"Processing schedules: {repr_(schedules)}")
        try:
            # 先构造课程列表，再构造课表
            schedule_classes = {i['name']: i['classes'] for i in schedules}
            built_lessons = {i['name']: [] for i in schedules}
            for name, classes in schedule_classes.items():
                for lesson in classes:
                    built_lessons[name].append(
                        st.Lesson(**lesson)
                    )
            log.debug(f"Built lessons: {repr_(built_lessons)}")

            # 从构造好的课程列表中构造课表
            new_schedule.schedules = st.Schedule([
                st.SingleDaySchedule(
                    enable_day=day['enable_day'],
                    classes=built_lessons[day['name']],
                    name=day['name'],
                    weeks=day['weeks'],
                )
                for day in schedules
            ])
            log.debug(f"Built schedules: {repr_(new_schedule.schedules)}")
        except pydantic.ValidationError as e:
            raise err.ParseError(f'课程数据有误: {data["schedules"]}') from e

        log.info(f"Created Schedule: {repr_(new_schedule)}")
        return new_schedule

    @classmethod
    def from_file(cls, fp: str) -> 'CSES':
        """
        从路径 ``fp`` 中读取并新建一个 CSES 课表对象。

        Args:
            fp (str): CSES 课程文件的路径。
        """
        with open(fp, encoding='utf8') as f:
            return CSES.from_str(f.read())

    def to_yaml(self) -> str:
        """
        将当前 CSES 课表对象转换为 YAML 字符串。

        Returns:
            str: 当前 CSES 课表对象的 YAML 字符串表示。
        """
        res = yaml.dump(self._gen_dict(),
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                        indent=2,
                        Dumper=utils.CustomizeDumper)
        log.debug(f"Generated YAML: {repr_(res)}")
        return res

    def to_file(self, fp: str, mode: str = 'w'):
        """
        将当前 CSES 课表对象转换为 YAML CSES 课程CSES入路径 ``fp`` 中。若文件夹/文件不存在，则会自动创建。

        Args:
            fp (str): 要写入的文件路径。
            mode (str, optional): 写入模式，默认值为 ``'w'`` ，即覆盖写入。
        """
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, mode, encoding='utf8') as f:
            f.write(self.to_yaml())
        log.info(f"Written CSES schedule file to {repr_(fp)}.")

    def _gen_dict(self) -> dict:
        """
        生成当前 CSES 课表对象的字典表示。

        Returns:
            dict: 当前 CSES 课表对象的字典表示。
        """
        return {
            'version': self.version,
            'subjects': [subject.model_dump() for subject in self.subjects.values()],
            'schedules': [schedule.model_dump() for schedule in self.schedules],
        }

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._gen_dict() == other._gen_dict()
        else:
            return NotImplemented
