#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_design_review.py
"""

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils import get_template
from tenacity import retry, stop_after_attempt, wait_fixed
from metagpt.actions.flutter_design_api import OUTPUT_MAPPING, templates

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software design architect, and your main task is to review the design. You need to ensure that the design conforms to the standards, is elegantly designed and modularized, easy to read and maintain, and is written in the requested format.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Design Review: Based on the following context and design, and following the check list, Provide key, clear, concise, and specific design modification suggestions, up to 5.
```
1. Check 0: Is the design implemented as per the requirements?
2. Check 1: Are there any issues with the design logic?
3. Check 2: Does the existing design follow the design definitions?
4. Check 3: Is there a function in the design that is omitted or not fully implemented that needs to be implemented?
5. Check 4: Does the design have unnecessary or lack dependencies?
```


## Design
-----
{design}


## Rewrite Design: Base on "Design Review" and the source design, rewrite design with triple quotes. Do your utmost to optimize THIS SINGLE FILE. 
-----
{context}
-----

"""

FORMAT_EXAMPLE = """

## Design Review
1. The design ...
2. ...
3. ...
4. ...
5. ...

## Rewrite Design:
{source_format_example}
"""


class WriteFlutterDesignReview(Action):
    def __init__(self, name="WriteFlutterDesignReview", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_design_review(self, prompt):
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        return system_design

    async def run(self, context, design):
        prompt_template, source_format_example = get_template(templates, "json")

        review_format_example = FORMAT_EXAMPLE.format(source_format_example=source_format_example)
        
        source_prompt = prompt_template.format(context=context, format_example=review_format_example)
        
        prompt = PROMPT_TEMPLATE.format(context=source_prompt, design=design)
        
        logger.info(f'Design review..')
        
        design = await self.write_design_review(prompt)
        return design, prompt
    