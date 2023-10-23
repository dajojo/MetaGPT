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
Role: You are a professional engineer; the main goal is to write compliant, elegant, modular, easy to read and maintain nullsafe dart code
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Code: {filename} Write code with triple quote, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Based on the context, implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW DEFINITIONS. DONT CHANGE ANY DESIGN.
5. Attention3: If the file contains a data class: use the freezed to pattern to implement it. 
6. Think before writing: What should be implemented and provided in this document?
7. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
8. ONLY IMPLEMENT ONE STATE CLASS PER FILE. DON'T FORGET the provider variable
9. Use the ResponseCollection if the state holds a list of data entities. 
10. USE either ConsumerStatefulWidget OR ConsumerWidget
-----
# Context
{context}
-----
## Format example
-----
## Code: {filename}
```dart
## {filename}
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SampleScreen extends ConsumerStatefulWidget {{
  Sample sample;
  SampleScreen({{required this.sample, super.key}});

  @override
  ConsumerState<ConsumerStatefulWidget> createState() => _SampleScreenState();
}}

class _SampleScreenState extends ConsumerState<SampleScreen> {{
  @override
  Widget build(BuildContext context) {{
    ChangeNotifierProvider<SampleController> controller = ref.watch(sampleControllerProvider)
    return SampleWidget()
  }}
}}

```
-----
"""


class WriteFlutterScreenClassCode(Action):
    def __init__(self, name="WriteFlutterScreenClassCode", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, context, filename):
        prompt = PROMPT_TEMPLATE.format(context=context, filename=filename)
        logger.info(f'Writing screen class {filename}..')
        code = await self.write_code(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code
    