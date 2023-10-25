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
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software engineer, and your main task is to review the code. You need to ensure that the code conforms to the standards, is elegantly designed and modularized, easy to read and maintain, and is written in NULLSAFE dart.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Fix Code: {filename} Base on 'Suggested Change' and 'Code', rewrite code with triple quotes. Do your utmost to optimize THIS SINGLE FILE. 
-----
# Suggested Change
{change}

## Code: {filename}
```
{code}
```
-----

## Format example
-----
{format_example}
-----

"""

FORMAT_EXAMPLE = """

## Code Review
1. The code ...
2. ...
3. ...
4. ...
5. ...

## Rewrite Code: {filename}
```dart
...
```
"""


class WriteFlutterCodeFix(Action):
    def __init__(self, name="WriteFlutterCodeFix", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, context,change, code, filename):
        format_example = FORMAT_EXAMPLE.format(filename=filename)
        prompt = PROMPT_TEMPLATE.format(context=context,change=change, code=code, filename=filename, format_example=format_example)
        logger.info(f'Code review {filename}..')
        code = await self.write_code(prompt)
        return code
    