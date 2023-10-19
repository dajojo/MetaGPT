#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : design_api.py
"""
import shutil
from pathlib import Path
from typing import List,Dict

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
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
Role: You are an architect; the goal is to design a SOTA Flutter system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, each section name is a key in json
Max Output: 8192 chars or 2048 tokens. Try to use them up.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Flutter package name: Provide as Python str with python triple quoto, concise and clear, characters only use a combination of all lowercase and underscores

## Feature list: Provided as Python dict[str,str], the keys represent the individual app specific features that are needed and have at least one dedicated screen (DONT INCLUDE COMMON FEATURES SUCH AS FIREBASE SERVICE). The values contain a brief description for each feature about the functionality and the assigned data classes, and functions. Each data class can be assigned to only one feature..

## Data classes: Use classDiagram code syntax, including classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Repository classes: Use classDiagram code syntax, including a Repository for each dataclass defining a communication interface to the backend (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Anything UNCLEAR: Provide as Plain text. Make clear here.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Implementation approach": "We will ...",
    "Flutter package name": "snake_game",
    "Feature list": {"authentication" : "Used to authenticate User. Required Functions: SignIn, SignOut, SignUp, PasswordReset"}
    "Data classes": '
    classDiagram
        class Game{
            int score
            ...
        }
        ...
    ',
    "Repository classes": '
    classDiagram
        GameRepository{
            create(Game) -> Game
            get(Game) -> Game
            ...
        }
        ...
    ',
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
Role: You are an architect; the goal is to design a SOTA Flutter system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Flutter package name: Provide as Python str with python triple quote, concise and clear, characters only use a combination of all lowercase and underscores

## Feature list: Provided as Python dict[str,str], the keys represent the individual app specific features that are needed and have at least one dedicated screen (DONT INCLUDE COMMON FEATURES SUCH AS FIREBASE SERVICE). The values contain a brief description for each feature about the functionality and the assigned data classes, and functions. Each data class can be assigned to only one feature..

## Data classes: Use classDiagram code syntax, including classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Repository classes: Use classDiagram code syntax, including a Repository for each dataclass defining a communication interface to the backend (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Anything UNCLEAR: Provide as Plain text. Make clear here.

""",
        "FORMAT_EXAMPLE": """
---
## Implementation approach
We will ...

## Flutter package name
```python
"snake_game"
```

## Feature list
```python
{ "authentication" : "Used to authenticate User. Data classes: User,... .Required Functions: SignIn, SignOut, SignUp, PasswordReset,..." }
```

## Data classes
```mermaid
classDiagram
    class Game{
        int score
        ...
    }
    ...

## Repository classes
```mermaid
classDiagram
    GameRepository{
        create(Game) -> Game
        get(Game) -> Game
        ...
    }
    ...
```

## Anything UNCLEAR
The requirement is clear to me.
---
""",
    },
}

OUTPUT_MAPPING = {
    "Implementation approach": (str, ...),
    "Flutter package name": (str, ...),
    "Feature list": (Dict[str,str], ...),
    "Data classes": (str, ...),
    "Repository classes": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteFlutterDesign(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = (
            "Based on the PRD, think about the system design, and design the corresponding APIs, "
            "data structures, library tables, processes, and paths. Please provide your design, feedback "
            "clearly and in detail."
        )

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def _save_prd(self, docs_path, resources_path, context):
        prd_file = docs_path / "prd.md"
        if context[-1].instruct_content and context[-1].instruct_content.dict()["Competitive Quadrant Chart"]:
            quadrant_chart = context[-1].instruct_content.dict()["Competitive Quadrant Chart"]
            await mermaid_to_file(quadrant_chart, resources_path / "competitive_analysis")

        if context[-1].instruct_content:
            logger.info(f"Saving PRD to {prd_file}")
            prd_file.write_text(json_to_markdown(context[-1].instruct_content.dict()))

    async def _save_system_design(self, docs_path, resources_path, system_design):
        data_classes = system_design.instruct_content.dict()[
            "Data classes"
        ]  # CodeParser.parse_code(block="Data structures and interface definitions", text=content)
        repository_classes = system_design.instruct_content.dict()[
            "Repository classes"
        ]  # CodeParser.parse_code(block="Program call flow", text=content)
        await mermaid_to_file(data_classes, resources_path / "data_api_design")
        await mermaid_to_file(repository_classes, resources_path / "seq_flow")
        system_design_file = docs_path / "system_design.md"
        logger.info(f"Saving System Designs to {system_design_file}")
        system_design_file.write_text((json_to_markdown(system_design.instruct_content.dict())))

    async def _save(self, context, system_design):
        if isinstance(system_design, ActionOutput):
            ws_name = system_design.instruct_content.dict()["Flutter package name"]
        else:
            ws_name = CodeParser.parse_str(block="Flutter package name", text=system_design)
        workspace = WORKSPACE_ROOT / ws_name
        self.recreate_workspace(workspace)
        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_prd(docs_path, resources_path, context)
        await self._save_system_design(docs_path, resources_path, system_design)

    async def run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)

        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        # fix Flutter package name, we can't system_design.instruct_content.python_package_name = "xxx" since "Flutter package name" contain space, have to use setattr
        
        setattr(
            system_design.instruct_content,
            "Flutter package name",
            system_design.instruct_content.dict()["Flutter package name"].strip().strip("'").strip('"'),
        )


        print("saving...")
        await self._save(context, system_design)
        return system_design
