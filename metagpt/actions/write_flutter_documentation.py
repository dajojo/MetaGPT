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
Role: You are a professional flutter Documentation writer; the main goal is to write compliant, elegant, modular, easy to read and maintain documentation. You are NOT allowed to change the code. Only add required comments for documentation purposes
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".
-----
# Context
{context}
-----
## Existing Code
The following is the existing code. Add Documentation comments according to the Flutter "dartdoc" standards. DO NOT CHANGE THE CODE!
-----
## Code: {filename}
```dart
{code}
```
## Format example:
Use the following as an example. DO NOT ALTER THE given CODE. Only add documentation comments as described in the following
-----
## Code: {filename}
```dart
/// {filename}
/// This is truly an amazing library.
/// {{@hideConstantImplementations}}

/// This top level constant will not show its implementation.
const a = 7;

/// {{@hideConstantImplementations}}
class A {{
  /// This constant will not show its implementation.
  static const aConst = 12;
}}

class B {{
  /// Despite the library directive, because this is a class
  /// member and there is no hideConstantImplementations
  /// directive on the class, we will show this implementation.
  static const bConst = 27; 
}}
...
```
-----
## Code: {filename} Write code with triple quote, based on the following list and context.
1. **File Overview**: Provide a general description of what the file does.
2. **Class Documentation**: Document the purpose and usage of each class defined in the file.
3. **Function Documentation**: Describe what each function does, its parameters, and return values.
4. **Variable Documentation**: Document the purpose of each variable.
5. **Constants Documentation**: Explain the purpose of any constants used.
6. **Enum Types Documentation**: Document any enumerated types and their values.
7. **Exception Documentation**: Document any exceptions that could be thrown.
8. **Deprecation Notices**: If applicable, include notices for deprecated code.
9. **Keep Code**: DO NOT CHANGE THE CODE. YOU ARE ONLY ALLOWED TO ADD THE DOCUMENTATION AS COMMENTS.
"""


class WriteFlutterDocumentation(Action):
    def __init__(self, name="WriteFlutterDocumentation", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, context,code, filename):
        logger.info(f'Got Code: {code}')
        prompt = PROMPT_TEMPLATE.format(context=context, code=code,filename=filename)
        logger.info(f'Writing Code to: {filename}')
        code = await self.write_code(prompt)
        logger.info(f"{code}")
        return code, prompt
    