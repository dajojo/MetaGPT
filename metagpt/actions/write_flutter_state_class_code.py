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

## Context
{context}
-----

## Code: {filename} Write code with triple quote, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Based on the context, implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW DEFINITIONS. DONT CHANGE ANY DESIGN.
5. Attention3: 'Sample' has to be replaced by the wanted data class name
6. Think before writing: What should be implemented and provided in this document?
7. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
8. ONLY IMPLEMENT ONE STATE CLASS PER FILE. DON'T FORGET the provider variable
9. Use the ResponseCollection if the state holds a list of data entities. 
10. 'Sample' refers to a placeholder. DO NOT include this in the final output
11. For states that require a list of elements, USE RESPONSE COLLECTION. It provides helpful tools and handles the next token it contains:
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
/// class SampleState
///  +void methodSample(sampleField1)
/// ...

import 'package:float_core/core/queried_list_collection/response_collection.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:float_core/core/utils/debug_tools.dart';
import 'package:float_core/core/utils/logger.dart';
import 'package:float_core/core/response/api_response.dart';
import 'package:float_apis/db/db_exception.dart';
import 'package:float_apis/db/entity/entity_list_state_notifier.dart';
import 'package:float_apis/db/entity/entity_state_notifier.dart';

final samplesStateProvider =
    StateNotifierProvider<SamplesState, ResponseCollection<Sample>>(
        (ref) => SamplesState(ref));

class SamplesState
    extends EntityListStateNotifier<Sample, SampleRepository> {{
    
  Sample? sample(String id) =>
      state.items.firstWhereOrNull((e) => e.id == id);

  SamplesState(Ref ref) : super(ref, sampleRepositoryProvider);

  late ProviderSubscription<AuthUser?> removeAuthStateListener;

  @override
  void startListeners() {{
    log("startingListeners");
    removeAuthStateListener = ref.listen(authStateProvider, (previous, next) {{
      if (next == null) {{
        state = ResponseCollection<Sample>();
      }} else {{
        list();
      }}
    }}, fireImmediately: true);
  }}

  @override
  Future<ApiResponse<QueriedList<Sample>, DBException>> list(
      {{List<DBWhere<dynamic>>? where}}) async {{

    AuthState userState = ref.read(authStateProvider.notifier);

    if (userState.userId == null) {{
      log("Can not load samples without user");
      return ApiError();
    }}

    SampleRepository repository = ref.read(repositoryProvider);

    state = state.copyWith(lastResponse: ApiLoading());
    ApiResponse<QueriedList<Sample>, DBException> res = (await repository
        .list(nextToken: state.nextToken, userId: userState.userId));

    if (res.isData) {{
      state = state.appendQueriedList(
        res,
        identifier: (object) => object.id,
      );
    }}

    return res;
  }}

  Future<ApiResponse<Sample?, FunctionsException>> randomSampleMethod1({{
    required String field1,
  }}) async {{
    SampleRepository repository =
        ref.read(sampleRepositoryProvider);

    var res = await repository.sampleMethod(sampleId: sampleId);

    if (res.isData && res.dataOrNull != null) {{
      state = state.appendItem(res.dataOrNull!, identifier: (e) => e.id);

      Sample2State sample2State = ref.read(sample2StateProvider.notifier);
      sample2State.sample2StateMethod(sampleId);
    }}

    return res;
  }}

  Future<ApiResponse<Sample, FunctionsException>> randomSampleMethod2({{
    required String field2,
  }}) async {{
    SampleRepository repository =
        ref.read(sampleRepositoryProvider);

    var res = await repository.sampleMethod(sampleId: sampleId);
    if (res.isData) {{
      state = state.copyWith(
          items: state.items.where((e) => e.id != res.dataOrNull!.id).toList());

      Sample2State sample2State = ref.read(sample2StateProvider.notifier);
      sample2State.sample2StateMethod2(sampleId);
    }}

    return res;
  }}
}}

```
-----
"""


class WriteFlutterStateClassCode(Action):
    def __init__(self, name="WriteFlutterStateClassCode", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, context,code,filename):
        prompt = PROMPT_TEMPLATE.format(context=context, filename=filename, code=code)
        logger.info(f'Writing state class {filename}..')
        code = await self.write_code(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code,prompt
    