"""``cseslib4py`` 所有的错误类型定义如下。"""


class CSESError(Exception):
    """所有由 ``cseslib4py`` 抛出的异常的基类。"""


class ParseError(CSESError):
    """解析 CSES 课程文件时抛出的异常。"""


class VersionError(CSESError):
    """解析 CSES 课程文件时，版本号错误抛出的异常。"""


class ValidationError(CSESError):
    """验证 CSES 课程文件时抛出的异常。"""
