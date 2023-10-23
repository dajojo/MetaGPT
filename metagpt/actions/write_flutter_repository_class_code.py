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
Role: You are a professional engineer; the main goal is to write compliant, elegant, modular, easy sample to read and maintain nullsafe dart code
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Code: {filename} Write code with triple quote, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Based on the context, implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW DEFINITIONS. DONT CHANGE ANY DESIGN.
5. Attention3: Use the freezed to pattern to implement data classes. 
6. Think before writing: What should be implemented and provided in this document?
7. ONLY IMPLEMENT ONE REPOSITORY CLASS PER FILE.
8. Never include any functions
-----
# Context
{context}
-----
## Format example
-----
## Code: {filename}
```dart
## {filename}
class SampleSerializer extends EntitySerializer<Sample> {{
  @override
  Sample beforeCreate(Sample e) {{
    return e.copyWith(
      id: IDGen.createID,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }}

  @override
  Sample beforeUpdate(Sample e) {{
    return e.copyWith(
        updatedAt: DateTime.now(), createdAt: e.createdAt ?? DateTime.now());
  }}

  @override
  Sample deserialize(Map<String, dynamic> json) {{
    return Sample.fromJson(json);
  }}

  @override
  Map<String, dynamic> serialize(Sample entity) {{
    return entity.toJson();
  }}

  @override
  String identifier(Sample e) {{
    return e.id!;
  }}
}}

Provider<SampleRepository> sampleRepositoryProvider =
    Provider((ref) => SampleRepository(ref));

class SampleRepository extends EntityRepository<Sample> {{
  static const String TABLE = "samples";

  SampleRepository(
    Ref ref,
  ) : super(
          ref: ref,
          table: TABLE,
          serializer: SampleSerializer(),
        );

  Future<ApiResponse<QueriedList<Sample>, DBException>> listFutureSamples(
      {{Object? nextToken, String? orderBy, bool ascending = false}}) {{
    DBApi dbApi = ref.read(dbApiProvider);

    return dbApi.list(
        where: [
          DBWhere.isGreaterThan(
              field: "start",
              object: DateTimeConverter().toJson(DateTime.now()))
        ],
        table: path(),
        orderBy: orderBy,
        ascending: ascending,
        nextToken:
            nextToken).then((value) =>
        value.mapData((data) => data.map((e) => serializer.deserialize(e))));
  }}

/*   @override
  Future<ApiResponse<QueriedList<Sample>, DBException>> list(
      {{Object? nextToken, String? orderBy, bool ascending = false}}) {{
    return super
        .list(nextToken: nextToken, orderBy: orderBy, ascending: ascending);
  }} */
}}


```
-----
"""


class WriteFlutterRepositoryClassCode(Action):
    def __init__(self, name="WriteFlutterRepositoryClassCode", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code


    async def run(self, context, filename):
        ### only load mermaid class def as context

        prompt = PROMPT_TEMPLATE.format(context=context, filename=filename)
        logger.info(f'Writing Repository class {filename}..')
        code = await self.write_code(prompt)
        return code,prompt
    