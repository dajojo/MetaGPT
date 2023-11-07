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
The following is the existing code. Add Documentation according to professional standards in markdown format.
-----
## Code: {filename}
```dart
{code}
```
## Format example:
Use the following as an example. Write the documentation for each file with respect to the code and the written documentation in context. Use simple markdown elements.
-----
## Code: {filename}
```markdown
Certainly! Below is an example of how you could structure a Markdown document to provide documentation for a Dart class as part of a Flutter project, without including the code itself:

```markdown
# `CustomButton` Class

The `CustomButton` class is a part of the Flutter project to provide a customizable button widget. This widget extends the Material button and adds additional styling and functionality.

## Properties

| Name | Type | Description |
| --- | --- | --- |
| `text` | `String` | The text displayed on the button. |
| `onPressed` | `Function` | The callback that is called when the button is tapped. |

## Methods

### `void handleTap()`

Handles the tap event and triggers the `onPressed` callback.
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
    