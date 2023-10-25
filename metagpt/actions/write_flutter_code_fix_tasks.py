#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code_review.py
"""

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import Message

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software engineer, and your main task is to fix the code. You need to ensure that the code conforms to the standards, is elegantly designed and modularized, easy to read and maintain, and is written in NULLSAFE dart.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

-----
# Context
{context}
-----
# Error
{error}
-----

## Code: {filename}
```
{code}
```
-----

## Format example
-----
{format_example}
-----


##  Code Fix Tasks: Provided as Markdown list. Ordered bullet point is a task, the more at the beginning, the more it is a prerequisite dependency, should be done first. 
File: list item specifies the affected file. Note, ONE file per task is allowed. 
The Operation point specifies the required operation. 
Choose from: 
WriteFlutterCode -> All purpose flutter code
WriteFlutterDataClassCode -> Must be used for generating data classes
WriteFlutterRepositoryClassCode -> Must be used for generating repository classes
WriteFlutterStateClassCode -> Must be used for generating state classes
WriteFlutterScreenClassCode -> Must be used for generating screen classes

## Based on "Error" and 'Code', list the required minimal changes per file. Stick to the Format example. DO NOT WRITE CODE!. Each Change only affects one file.

"""

FORMAT_EXAMPLE = """

## Code Fix Tasks

1. [ ] Change the ...
    - File: lib/..../file.dart
    - Operation: WriteFlutterCode

2. [ ] Change the ...
    - File: lib/..../file2.dart
    - Operation: WriteFlutterCode

"""


class WriteFlutterCodeFixTasks(Action):
    def __init__(self, name="WriteFlutterCodeFixTasks", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    async def run(self,context, error, code, file_path):
        format_example = FORMAT_EXAMPLE.format()
        prompt = PROMPT_TEMPLATE.format(context=context,error=error, code=code, filename=file_path, format_example=format_example)
        logger.info(f'Code fix {file_path}..')
        code_fix_tasks = await self._aask(prompt)
        return code_fix_tasks
    