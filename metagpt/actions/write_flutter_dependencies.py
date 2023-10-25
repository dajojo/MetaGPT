#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code.py
"""
from metagpt.actions import WriteDesign
from metagpt.actions.action import Action
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional flutter engineer; the main goal is to write compliant, elegant, modular, easy to read and maintain nullsafe dart code
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".
-----
# Context
{context}
-----
## Format example:
Use the following as a blueprint. The code response MUST look like this but REPLACE everything containing 'Sample' and insert the code which solves the tasks.
-----
## Code: {filename}
```yaml
{code}
...
```
-----

## Code: {filename} Write code with triple quote, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING DEPENDENCIES.
2. Think before writing: What should be implemented and provided in this document?

"""


class WriteFlutterDependencies(Action):
    def __init__(self, name="WriteFlutterDependencies", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, context, code, filename = "pubspec.yaml"):
        prompt = PROMPT_TEMPLATE.format(context=context, filename=filename,code=code)
        logger.info(f'Writing Code {filename}..')
        code = await self.write_code(prompt)
        return code, prompt
    