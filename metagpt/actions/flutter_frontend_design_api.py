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

templates = {"markdown": {
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

## File tree: Provided as Markdown, specify the content of the flutter lib directory. Use a feature based approach where you assign each feature a directory containing the domain, repository, states, screens and view controllers. Use only features that are defined in the feature list!. Every filename must inlcude a brief description about the content. Every STATE and REPOSITORY FILE must only be introduced ONCE!. Folder names domain, states, repositories, screens and controllers must not be changed!

## State classes: Use classDiagram code syntax, including state classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. The state will be stored as a Riverpod AsyncValue which handles Error and loading states.

## Controller: Use classDiagram code syntax, including controller classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Screens: Use classDiagram code syntax, including screens classes (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes (listen hierarchy), and comply with professional standards. The state structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. Also specify if stateful or stateless has to be used.

## API classes: Use classDiagram code syntax, including a Device API Repository for necessary device apis such as Media Gallery, Camera, Sensors, Location,... Defining a communication interface to the Hardware (with type annotations). Comply with professional standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. Dont include any Backend APIs since they are already covered. 

## 3rd Party Dependencies: ADD all required dependencies. Separate between dependencies and dev_dependencies. Keep the dependencies defined in the FORMAT EXAMPLE.

## Anything UNCLEAR: Provide as Plain text. Make clear here.

""",
"FORMAT_EXAMPLE": """
---

## File tree
- lib
    - main.dart: runApp and other stuff...
    - home.dart: tabs are specified here..
    - features
        - sample_feature
            - domain
                - sample_data.dart: This contains sample data class
                - sample_type.dart: Custom Enum used in sample data
            - states
                - sample_state.dart: List entity state of sample data
            - repositories
                - sample_repository.dart: Repository for backend functions
            - screens
                - sample_screen.dart: Update and Edit data class
            - controller
                - sample_view_controller.dart: Controller for sample_screen.dart
            - components
                - sample_button.dart: Special button used for screens in this feature

## 3rd Party Dependencies
- dependencies
    - flutter:
        sdk: flutter
    - flutter_localizations:
        sdk: flutter
    - cloud_firestore: null
    - cloud_functions: null
    - flutter_riverpod: null
    - freezed_annotation: null
    - firebase_auth: null
    - firebase_core: null
    - firebase_dynamic_links: null
    - firebase_messaging: null
    - firebase_storage: null
    - json_annotation: null
    - permission_handler: null
    - flutter_platform_widgets: null
    - float_apis:
        path: ./packages/float_apis
    - float_core:
        path: ./packages/float_core
    - uuid: null
    ...

- dev_dependencies
    - build_runner: null
    - freezed: null
    - json_serializable: null
    - flutter_test:
        sdk: flutter
    ...

## State classes
```mermaid
classDiagram
    class SamplesState {
        listenTo([OtherSampleState,OtherSampleState2])
        sampleMethod1()
        AddAnotherInstanceSample()
        ...
    }
    class OtherSampleState {
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

 ## API classes
```mermaid
classDiagram
    class SampleApi {
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


class WriteFlutterFrontendDesign(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = (
            "Based on the Architecture Design, think about the frontend system design, and design the corresponding flutter project file structure, domain, states, screens, components and view controller."
            "Use the Riverpod state management library for state classes and view controllers."
            "Please provide your design, feedback clearly and in detail."
        )


    async def run(self, context, format="markdown"):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        system_design = await self._aask(prompt)
        
        return system_design
