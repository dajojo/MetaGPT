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
from metagpt.schema import Message

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
Attention: DONT USE triple dots like "..." Include all necessary information!

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Feature list: Provided as Python dict[str,str], the keys represent the individual app specific features that are needed and have at least one dedicated screen and a dedicated function (DONT INCLUDE COMMON and OBVIOUS FEATURES SUCH AS 'Connection Service' or 'User Interface'). The values contain a brief description for each feature about the functionality and the assigned data classes, and functions. Each data and state class can be assigned to only one feature. Use lower_snake_case.

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
    "Feature list": {"sample_feature" : "Used to for ....  Functions: ... , Data classes ..."},
    "Data classes": '
    classDiagram
        class Game{
            int score
        }
        ...
    ',
    "Repository classes": '
    classDiagram
        GameRepository{
            create(Game) -> Game
            get(Game) -> Game
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
Attention: DONT USE triple dots like "..." Include all necessary information!

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Feature list: Provided as Python dict[str,str], the keys represent the individual app specific features that are needed and have at least one dedicated screen and a dedicated function (DONT INCLUDE COMMON and OBVIOUS FEATURES SUCH AS 'Connection Service' or 'User Interface'). The values contain a brief description for each feature about the functionality and the assigned data classes, and functions. Each data and state class can be assigned to only one feature. Use lower_snake_case.

## Data classes: Use classDiagram code syntax, including classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Repository classes: Use classDiagram code syntax, including a Repository for each dataclass defining a communication interface to the backend (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Anything UNCLEAR: Provide as Plain text. Make clear here.
""",
"FORMAT_EXAMPLE": """
---
## Implementation approach
We will ...

## Feature list
```python
    {"sample_feature" : "Used to for ....  Functions: ... , Data classes ..."}
```

## Data classes
```mermaid
classDiagram
    class Game{
        int score
    }
    ...
```

## Repository classes
```mermaid
classDiagram
    GameRepository{
        create(Game) -> Game
        get(Game) -> Game
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

    async def run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)

        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        
        return system_design
