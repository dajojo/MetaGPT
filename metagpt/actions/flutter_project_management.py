#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
"""
from typing import List

import re

from metagpt.actions.action import Action
from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.logs import logger
from metagpt.schema import Message



#### Create new project!

templates = {
"markdown": {
"PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.
Attention: DONT USE triple dots like "..." Include all necessary information!

## Task list: Provided as Markdown list. Ordered bullet point is a task, the more at the beginning, the more it is a prerequisite dependency, should be done first. 
File: list item specifies the affected file. Note, ONE file per task is allowed. 
The Operation point specifies the required operation. 
Choose from: 
WriteFlutterCode -> All purpose flutter code
WriteFlutterDataClassCode -> Must be used for generating data classes
WriteFlutterRepositoryClassCode -> Must be used for generating repository classes
WriteFlutterStateClassCode -> Must be used for generating state classes
WriteFlutterScreenClassCode -> Must be used for generating screen classes
WriteFlutterDependencies -> Must be used for changeing the dependencies

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

In the example "..." is included to indicate there might be more. THIS IS NOT ALLOWED IN THE OUTPUT. Include all necessary information!
Changes in folder 'packages' are prohibited! This code must not be changed!
""",
"FORMAT_EXAMPLE": '''
---

## Task list
1. [ ] Adjust pubspec.yaml ....
    - File: pubspec.yaml
    - Operation: WriteFlutterDependencies
2. [ ] Implement main.dart ....
    - File: lib/main.dart
    - Operation: WriteFlutterCode
3. [ ] Implement home.dart including tabs ...
    - File: lib/home.dart
    - Operation: WriteFlutterCode
4. [ ] Implement sample_file.dart as specified in ...
    - File: lib/.../domain/sample_file.dart
    - Operation: WriteFlutterDataClassCode
5. [ ] Implement sample_repository_file.dart as specified ...
    - File: lib/.../repositories/sample_file.dart
    - Operation: WriteFlutterRepositoryClassCode
6. [ ] Implement sample_state_file.dart as specified in ...
    - File: lib/.../states/sample_state.dart
    - Operation: WriteFlutterStateClassCode
7. [ ] Implement sample_screen_file.dart as specified in ...
    - File: lib/.../states/sample_state.dart
    - Operation: WriteFlutterScreenClassCode
...


## Anything UNCLEAR
We need ... how to start.
---
''',
    },
}


class WriteFlutterTasks(Action):
    def __init__(self, name="CreateFlutterTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, format="markdown"):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        rsp = await self._aask(prompt)
        return rsp


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
