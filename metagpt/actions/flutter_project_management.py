#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
"""
from typing import List

from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information, each section name is a key in json. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Flutter third-party packages: Provided in pubspec.yaml format

## Full API spec: List all Entity and their corresponding operations and cloud functions including input and output. Describe all APIs that may be used by both frontend and backend.

## Logic Analysis: Provided as a Python list[list[str]. the first is filename including relative path with reference to the lib folder, the second is class/method/function should be implemented in this file. Use a feature based folder structure. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": '''
{
    "Required Flutter third-party packages": [
        "sample_package1: ^2.2.4",
        "sample_package2: null"
    ],
    "Full API spec": """
        Entities:
            - SampleEntity1:
                - create
                - get
                - update
                - delete
                - list
                ....
            - SampleEntity2:
                - create
                - list
                - subscribe
                ...
            ...
        Cloud Functions: 
            - sampleCloudFunction(SampleEntity1 input) -> SampleEntity2
            ...
     """,
    "Logic Analysis": [
        ["lib/.../sample_file.dart","Contains..."]
    ],
    "Task list": [
        "lib/.../sample_file.dart"
    ],
    "Shared Knowledge": """
        'lib/.../sample_file.dart' contains ...
    """,
    "Anything UNCLEAR": "We need ... how to start."
}
''',
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information, note that all sections are returned in Python code triple quote form separately. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Flutter third-party packages: Provided in pubspec.yaml format

## Full API spec: List all Entity and their corresponding API Operations and Cloud Functions including input and output. Describe all APIs that may be used by both frontend and backend.

## Logic Analysis: Provided as a Python list[list[str]. the first is filename including relative path with reference to the lib folder, the second is class/method/function should be implemented in this file. Use a feature based folder structure. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

""",
        "FORMAT_EXAMPLE": '''
---
## Required Flutter third-party packages
```yaml
"""
sample_package1: ^2.2.4,
sample_package2: null,
"""
```

## Full API spec
```python
"""
Entities:
    - SampleEntity1:
        - create
        - get
        - update
        - delete
        - list
        ....
    - SampleEntity2:
        - create
        - list
        - subscribe
        ...
    ...
Cloud Functions: 
    - sampleCloudFunction(SampleEntity1 input) -> SampleEntity2
    ...
"""
```

## Logic Analysis
```dart
[
    ["lib/.../sample_file.dart","Contains..."]
]
```

## Task list
```dart
[
    "lib/.../sample_file.dart",
]
```

## Shared Knowledge
```dart
"""
'lib/.../sample_file.dart' contains ...
"""
```

## Anything UNCLEAR
We need ... how to start.
---
''',
    },
}
OUTPUT_MAPPING = {
    "Required Flutter third-party packages": (List[str], ...),
    "Full API spec": (str, ...),
    "Logic Analysis": (List[List[str]], ...),
    "Task list": (List[str], ...),
    "Shared Knowledge": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteFlutterTasks(Action):
    def __init__(self, name="CreateTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    def _save(self, context, rsp):

        print(f"DEBUG: context {context[-1]} {context}")


        if context[-1].instruct_content:
            ws_name = context[-1].instruct_content.dict()["Flutter package name"]
        else:
            ws_name = CodeParser.parse_str(block="Flutter package name", text=context[-1].content)
        file_path = WORKSPACE_ROOT / ws_name / "docs/api_spec_and_tasks.md"
        file_path.write_text(json_to_markdown(rsp.instruct_content.dict()))

        # Write requirements.txt
        requirements_path = WORKSPACE_ROOT / ws_name / "pubspec.yaml"
        requirements_path.write_text("\n".join(rsp.instruct_content.dict().get("Required Flutter third-party packages")))

    async def run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING, format=format)
        self._save(context, rsp)
        return rsp


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
