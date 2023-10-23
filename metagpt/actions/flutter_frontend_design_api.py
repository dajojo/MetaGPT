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
Role: You are an frontend architect; the goal is to design a SOTA Flutter frontend system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, each section name is a key in json
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: DONT USE triple dots like "..." Include all necessary information!

## File tree: Provided as Python dict[str,dict], specify the content of the flutter lib directory. Use a feature based approach where you assign each feature a directory containing the domain, repository, states, screens and view controllers. Use only features that are defined in the feature list!. Every filename must map to a brief description containing only one sentence. Every state and repository can only be introduced once!. Folder names domain, states, repositories, screens and controllers must not be changed!

## State classes: Use classDiagram code syntax, including state classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Controller: Use classDiagram code syntax, including controller classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Screens: Use classDiagram code syntax, including screens classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. Also specify if stateful or stateless has to be used.

## Device API classes: Use classDiagram code syntax, including a Device API Repository for necessary device apis such as Media Gallery, Camera, Sensors, Location,... Defining a communication interface to the Hardware (with type annotations). Comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. Dont include any Backend APIs since they are already covered. 

## Anything UNCLEAR: Provide as Plain text. Make clear here.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "File tree": 
    {"lib" : {
        "main.dart": "runApp and other stuff...", 
        "home.dart": "tabs are specified here..", 
        "features": {
            "sample_feature":    
                {"domain":
                    {
                        "sample_data.dart": "Sample data class",
                        "sample_type.dart": "Custom Enum used in sample data"
                    },
                "states":
                    {
                        "sample_state.dart": "List entity state of sample data"
                    },
                "repositories":
                    {
                        "sample_repository.dart": "Repository for backend functions"
                    },
                "screens":
                    {
                        "sample_screen.dart": "Update and Edit data class"
                    },
                "controller":
                    {
                        "sample_view_controller.dart": "Controller for sample_screen.dart"
                    },
                "components":
                    {
                        "sample_button.dart": "Special button used for screens in this feature"
                    },
                }
            }
        }
    },
    "State classes": '
    classDiagram
        class SampleState extends EntityListStateNotifier{
            listenTo([OtherSampleState,OtherSampleState2])
            sampleMethod1()
            AddAnotherInstanceSample()
            ...
        }
        ...
    ',

    "Controller": '
    classDiagram
        class SampleController {
            listenTo([OtherSampleState,OtherSampleState2])
            sampleMethod1()
            AddAnotherInstanceSample()
            validateSampleTextInput1()
            ...
        }
        ...
    ',

    "Screens": '
    classDiagram
        class SampleScreen extends StatelessConsumer {
            listenTo([SampleController])
            onSampleButtonClick1()
            onTextEdited2()
            ...
        }
        ...
    ',
    "Device API classes": '
    classDiagram
        class MediaApi {
            takePicture
            pickFromGallery
            ...
        }
        class LocationApi{
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
Role: You are an frontend architect; the goal is to design a SOTA Flutter frontend system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.
Attention: DONT USE triple dots like "..." Include all necessary information!

## File tree: Provided as Python dict[str,dict], specify the content of the flutter lib directory. Use a feature based approach where you assign each feature a directory containing the domain, repository, states, screens and view controllers. Use only features that are defined in the feature list!. Every filename must map to a brief description containing only one sentence. Every STATE and REPOSITORY FILE must only be introduced ONCE!. Folder names domain, states, repositories, screens and controllers must not be changed!

## State classes: Use classDiagram code syntax, including state classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. The state will be stored as a Riverpod AsyncValue which handles Error and loading states.

## Controller: Use classDiagram code syntax, including controller classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Screens: Use classDiagram code syntax, including screens classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. Also specify if stateful or stateless has to be used.

## Device API classes: Use classDiagram code syntax, including a Device API Repository for necessary device apis such as Media Gallery, Camera, Sensors, Location,... Defining a communication interface to the Hardware (with type annotations). Comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. Dont include any Backend APIs since they are already covered. 

## Anything UNCLEAR: Provide as Plain text. Make clear here.

""",
"FORMAT_EXAMPLE": """
---

## File tree
```python
    {"lib" : {
        "main.dart": "runApp and other stuff...", 
        "home.dart": "tabs are specified here..", 
        "features": {
            "sample_feature":    
                {"domain":
                    {
                        "sample_data.dart":"This contains sample data class"
                        "sample_type.dart": "Custom Enum used in sample data"                           
                    },
                "states":
                    {
                        "sample_state.dart":  "List entity state of sample data"
                    },
                "repositories":
                    {
                        "sample_repository.dart": "Repository for backend functions"
                    },
                "screens":
                    {
                        "sample_screen.dart": "Update and Edit data class"
                    },
                "controller":
                    {
                        "sample_view_controller.dart":"Controller for sample_screen.dart"
                    },
                "components":
                    {
                        "sample_button.dart": "Special button used for screens in this feature"
                    },
                }
            }
        }
    }
```

## State classes
```mermaid
classDiagram
    class SampleState {
        listenTo([OtherSampleState,OtherSampleState2])
        sampleMethod1()
        AddAnotherInstanceSample()
        ...
    }
    ...
```

## Controller
```mermaid
classDiagram
    class SampleController {
        listenTo([OtherSampleState,OtherSampleState2])
        sampleMethod1()
        AddAnotherInstanceSample()
        validateSampleTextInput1()
        ...
    }
    ...
```

## Screens
```mermaid
classDiagram
    class SampleScreen extends StatelessConsumer {
        listenTo([SampleController])
        onSampleButtonClick1()
        onTextEdited2()
        ...
    }
    ...
```

 ## Device API classes
```mermaid
classDiagram
    class MediaApi {
        takePicture
        pickFromGallery
        ...
    }
    class LocationApi{
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
    "File tree": (Dict[str,Dict], ...),
    "State classes": (str, ...),
    "Controller": (str, ...),
    "Screens": (str, ...),
    "Device API classes": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteFlutterFrontendDesign(Action):
    def __init__(self, name, context=None, llm=None):
        logger.info("Init Frontend Design")
        super().__init__(name, context, llm)
        self.desc = (
            "Based on the Architecture Design, think about the frontend system design, and design the corresponding flutter project file structure, domain, states, screens, components and view controller."
            "Use the Riverpod state management library for state classes and view controllers."
            "Please provide your design, feedback clearly and in detail."
        )


    async def run(self, context, format=CONFIG.prompt_format):
        #logger.info("Running Frontend Design")
        prompt_template, format_example = get_template(templates, format)
        #logger.info("Got template")
        prompt = prompt_template.format(context=context, format_example=format_example)
        #logger.info(f"Got prompt {prompt}")
        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "frontend_system_design", OUTPUT_MAPPING, format=format)
        
        return system_design
