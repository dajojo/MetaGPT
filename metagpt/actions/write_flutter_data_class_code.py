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
from metagpt.flutter_common import get_workspace
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed
import re
from pathlib import Path

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer; the main goal is to write compliant, elegant, modular, easy to read and maintain nullsafe dart code
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Context
{context}
-----

## Code: {filename} Write code with triple quote, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Based on the context, implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW DEFINITIONS. DONT CHANGE ANY DESIGN.
5. Attention3: Use the freezed to pattern to implement data classes. 
6. Think before writing: What should be implemented and provided in this document?
7. ONLY IMPLEMENT ONE DATA CLASS PER FILE.
8. NEVER use the 'required' annotation. ALWAYS make it nullable using the 'Type?' annotation.
9. All id, createdAt, updatedAt are mandatory. @SampleTypeConverter is necessary if custom enums are used.
10. Never include any functions
11. 'Sample' refers to a placeholder. DO NOT include this in the final output

-----
## Existing Code
The following is the existing code. Try to achieve all goals using minimal changes.
-----
## Code: {filename}
```dart
{code}
```
## Format example
Use the following as an example. The code response MUST look like this but REPLACE everything containing 'Sample' and insert the code which solves the tasks.

-----
## Code: {filename}
```dart
/// {filename}
/// This file contains... 
/// classdiagramm:
/// class Sample
///  +void methodSample(sampleField1)
/// ...
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:float_core/core/utils/debug_tools.dart';
import 'package:float_core/core/utils/logger.dart';
import 'package:float_core/core/response/api_response.dart';
import 'package:float_apis/db/db_exception.dart';
import 'package:float_apis/db/entity/entity_list_state_notifier.dart';
import 'package:float_apis/db/entity/entity_state_notifier.dart';

part 'sample.g.dart';
part 'sample.freezed.dart';

@freezed
class Sample with _$Sample, Entity {{
  Sample._();

  @TimeStampDateTimeConverter()
  @SampleTypeConverter()
  factory Sample(
      {{String? id,
      SampleType? sampleField1,
      String? sampleField2,
      FileReference? sampleFileReference,
      DateTime? createdAt,
      DateTime? updatedAt,
      @Default(false) bool deleted}}) = _Sample;

  factory Sample.fromJson(Map<String, dynamic> json) => _$SampleFromJson(json);
}}

```
-----
"""


class WriteFlutterDataClassCode(Action):
    def __init__(self, name="WriteFlutterDataClassCode", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code


    async def run(self, context, code,filename):
        ### only load mermaid class def as context

        prompt = PROMPT_TEMPLATE.format(context=context,code=code, filename=filename)
        logger.info(f'Writing Data class {filename}..')
        code = await self.write_code(prompt)
        return code, prompt
    