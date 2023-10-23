#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
from pathlib import Path
from typing import List,Dict
import re

from metagpt.actions import Action, ActionOutput
from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.flutter_common import get_workspace
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.mermaid import mermaid_to_file

templates = {
        "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are an backend architect; the goal is to design a SOTA Flutter backend system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, each section name is a key in json
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: DONT USE triple dots like "..." Include all necessary information!

## Full API spec: List all Entity and their corresponding API Operations and Cloud Functions including input and output. Describe all APIs that may be used by both frontend and backend.

## Anything UNCLEAR: Provide as Plain text. Make clear here.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "File tree": 
    "Full API spec": '''
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
     ''',
    "Anything UNCLEAR": "The requirement is clear to me."
}
[/CONTENT]
""",
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are an backend architect; the goal is to design a SOTA Flutter backend system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.
Attention: DONT USE triple dots like "..." Include all necessary information!

## Full API spec: List all Entity and their corresponding API Operations and Cloud Functions including input and output. Describe all APIs that may be used by both frontend and backend.

## Anything UNCLEAR: Provide as Plain text. Make clear here.
In the example "..." is included to indicate there might be more. THIS IS NOT ALLOWED IN THE OUTPUT. Include all necessary information!
""",
        "FORMAT_EXAMPLE": """
---

## Full API spec
```python
'''
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
'''
```


## Anything UNCLEAR
The requirement is clear to me.
---
""",
    },
}

OUTPUT_MAPPING = {
    "Full API spec": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteFlutterBackendDesign(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = (
            "Based on the Architecture Design, think about the backend system design, and design the corresponding flutter project file structure, state classes, screens, components and view controller."
            "Use the Riverpod state management library for state classes and view controllers."
            "Please provide your design, feedback clearly and in detail."
        )

    async def _save_system_design(self, docs_path, resources_path, system_design):
        data_classes = system_design.instruct_content.dict()[
            "State classes"
        ]  # CodeParser.parse_code(block="Data structures and interface definitions", text=content)
        repository_classes = system_design.instruct_content.dict()[
            "Device API classes"
        ]  # CodeParser.parse_code(block="Program call flow", text=content)
        await mermaid_to_file(data_classes, resources_path / "state_classes")
        await mermaid_to_file(repository_classes, resources_path / "device_api_classes")
        system_design_file = docs_path / "backend_system_design.md"
        logger.info(f"Saving System Designs to {system_design_file}")
        system_design_file.write_text((json_to_markdown(system_design.instruct_content.dict())))

    async def _save(self, context, system_design):
        workspace = get_workspace(self)
        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_system_design(docs_path, resources_path, system_design)

    async def run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)

        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "backend_system_design", OUTPUT_MAPPING, format=format)
        # fix Flutter package name, we can't system_design.instruct_content.python_package_name = "xxx" since "Flutter package name" contain space, have to use setattr
        
        await self._save(context, system_design)
        return system_design
