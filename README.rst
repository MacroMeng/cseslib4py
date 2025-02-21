.. image:: https://static.smart-teach.cn/logos/full.jpg
   :height: 64

PyCSES
======

一个用于解析与生成 CSES 格式的 Python 库，提供简单易用的 API。  
详细示例请见 [cses/__init__.py](cses/__init__.py)。

安装
----

.. code-block:: console

   pip install pycses

使用示例
--------

.. code-block:: python

import cses

# Read a CSES file
parser = cses.CSESParser("path/to/file.cses.yaml")

# Check if the file is valid
if not cses.CSESParser.is_cses_file("path/to/file.cses.yaml"):
    print("Not a valid CSES file")

# Get subjects
for subject in parser.get_subjects():
    print("Name:", subject["name"])
    print("Simplified Name:", subject["simplified_name"])
    print("Teacher:", subject["teacher"])
    print("Room:", subject["room"])
    print("")

# Get schedules
for schedule in parser.get_schedules():
    print("Name:", schedule["name"])
    print("Enable Day:", schedule["enable_day"])
    print("Weeks:", schedule["weeks"])
    print("Classes:")
    for class_ in schedule["classes"]:
        print("  Subject:", class_["subject"])
        print("  Start Time:", class_["start_time"])
        print("  End Time:", class_["end_time"])
    print("")


# Generate a CSES file
generator = cses.CSESGenerator(version=1)

# Add a subject
generator.add_subject(name="Math", simplified_name="M", teacher="Mr. Wang", room="101")

# Add a schedule
generator.add_schedule(name="Monday", enable_day="mon", weeks=all, classes=[
    {
        "subject": "Math",
        "start_time": "08:00",
        "end_time": "09:00"
    },
    {
        "subject": "Biology",
        "start_time": "09:00",
        "end_time": "10:00"
    }
])

# Save the file
generator.save_to_file("path/to/file.cses.yaml")
   ...

更多信息
--------

请参阅 [README.md](README.md) 或 [LICENSE](LICENSE) 获取更多说明。