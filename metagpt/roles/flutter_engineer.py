#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : engineer.py
"""
import asyncio
import shutil
from collections import OrderedDict
from pathlib import Path

from metagpt.actions import WriteCode, WriteCodeReview, WriteDesign, WriteTasks
from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.actions.flutter_frontend_design_api import WriteFlutterFrontendDesign
from metagpt.actions.flutter_project_management import WriteFlutterTasks
from metagpt.actions.write_flutter_code import WriteFlutterCode
from metagpt.actions.write_flutter_code_review import WriteFlutterCodeReview
from metagpt.actions.write_flutter_data_class_code import WriteFlutterDataClassCode
from metagpt.actions.write_flutter_repository_class_code import WriteFlutterRepositoryClassCode
from metagpt.actions.write_flutter_screen_class_code import WriteFlutterScreenClassCode
from metagpt.actions.write_flutter_state_class_code import WriteFlutterStateClassCode
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from metagpt.utils.special_tokens import FILENAME_CODE_SEP, MSG_SEP
from metagpt.flutter_common import get_workspace, to_camel_case
import re

async def gather_ordered_k(coros, k) -> list:
    tasks = OrderedDict()
    results = [None] * len(coros)
    done_queue = asyncio.Queue()

    for i, coro in enumerate(coros):
        if len(tasks) >= k:
            done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                index = tasks.pop(task)
                await done_queue.put((index, task.result()))
        task = asyncio.create_task(coro)
        tasks[task] = i

    if tasks:
        done, _ = await asyncio.wait(tasks.keys())
        for task in done:
            index = tasks[task]
            await done_queue.put((index, task.result()))

    while not done_queue.empty():
        index, result = await done_queue.get()
        results[index] = result

    return results


class FlutterEngineer(Role):
    """
    Represents an Engineer role responsible for writing and possibly reviewing code.

    Attributes:
        name (str): Name of the engineer.
        profile (str): Role profile, default is 'Engineer'.
        goal (str): Goal of the engineer.
        constraints (str): Constraints for the engineer.
        n_borg (int): Number of borgs.
        use_code_review (bool): Whether to use code review.
        todos (list): List of tasks.
    """

    def __init__(
        self,
        name: str = "Alex",
        profile: str = "FlutterEngineer",
        goal: str = "Write elegant, readable, extensible, efficient Dart code",
        constraints: str = "The code should conform to standards and be modular and maintainable",
        n_borg: int = 1,
        use_code_review: bool = False,
    ) -> None:
        """Initializes the Engineer role with given attributes."""
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteFlutterCode])
        self.use_code_review = use_code_review
        if self.use_code_review:
            self._init_actions([WriteFlutterCode, WriteFlutterCodeReview])
        self._watch([WriteFlutterTasks])
        self.todos = []
        self.n_borg = n_borg

    @classmethod
    def parse_tasks(self, task_msg: Message) -> list[str]:
        if task_msg.instruct_content:
            return task_msg.instruct_content.dict().get("Task list")
        return CodeParser.parse_file_list(block="Task list", text=task_msg.content)

    @classmethod
    def parse_code(self, code_text: str) -> str:
        return CodeParser.parse_code(block="", text=code_text)

    @classmethod
    def parse_workspace(cls, system_design_msg: Message) -> str:
        if system_design_msg.instruct_content:
            return system_design_msg.instruct_content.dict().get("Flutter package name").strip().strip("'").strip('"')
        return CodeParser.parse_str(block="Flutter package name", text=system_design_msg.content)

    def get_class_spec(self,class_name, markdown_content):
        # Regular expression to extract the class specification
        pattern = r'class {}{{(.*?)}}'.format(class_name)
        match = re.search(pattern, markdown_content, re.DOTALL)
        
        # If match is found, return the specification, otherwise return None
        if match:
            class_spec = "class {}{{".format(class_name) + match.group(1) + "}"
            return class_spec.strip()
        else:
            return None

    def get_file_tree(self,markdown_content):
        lines = markdown_content.split("\n")
        
        tree = []

        for line in lines:
            if "## State classes" in line:
                break
            tree.append(line)

        return "\n".join(tree)


    def read_markdown_file(self,filename):
        with open(filename, 'r') as file:
            content = file.read()
        return content


    def write_file(self, filename: str, code: str):
        workspace = get_workspace(self)
        filename = filename.replace('"', "").replace("\n", "")
        file = workspace / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code)
        return file

    def recv(self, message: Message) -> None:
        self._rc.memory.add(message)
        if message in self._rc.important_memory:
            self.todos = self.parse_tasks(message)

    async def _act_mp(self) -> Message:
        # self.recreate_workspace()
        todo_coros = []
        for todo in self.todos:
            todo_coro = WriteCode().run(
                context=self._rc.memory.get_by_actions([WriteTasks, WriteDesign]), filename=todo
            )
            todo_coros.append(todo_coro)

        rsps = await gather_ordered_k(todo_coros, self.n_borg)
        for todo, code_rsp in zip(self.todos, rsps):
            _ = self.parse_code(code_rsp)
            logger.info(todo)
            logger.info(code_rsp)
            # self.write_file(todo, code)
            msg = Message(content=code_rsp, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)
            del self.todos[0]

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(content="all done.", role=self.profile, cause_by=type(self._rc.todo))
        return msg

    async def _act_sp(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        ws = get_workspace(self)

        frontend_sys_spec = self.read_markdown_file(ws/ "docs"/ "frontend_system_design.md")
        tree = self.get_file_tree(frontend_sys_spec)

        for todo in self.todos:
            todo_file_name = to_camel_case(Path(todo).name)[:-4]

            if "/domain/" in todo:
                ## data class
                data_class = todo_file_name
                sys_spec = self.read_markdown_file(ws/ "docs"/ "system_design.md")
                class_spec = self.get_class_spec(data_class,sys_spec)
                if class_spec != None:
                    context = tree +"\n"+class_spec
                else:
                    logger.warning(f"Warning! Using full history for {todo} {data_class}")
                    context = self._rc.history
                code, prompt = await WriteFlutterDataClassCode().run(context=context, filename=todo)
            
            elif "/repositories/" in todo:
                ## repository class
                repository_class = todo_file_name ### user_repository
                sys_spec = self.read_markdown_file(ws/ "docs"/ "system_design.md")
                class_spec = self.get_class_spec(repository_class,sys_spec)
                if class_spec != None:
                    context = tree +"\n"+class_spec
                else:
                    logger.warning(f"Warning! Using full history for {todo}")
                    context = self._rc.history
                code, prompt = await WriteFlutterRepositoryClassCode().run(context=context, filename=todo)

            elif "/states/" in todo:
                ## state class 
                state_class = todo_file_name
                class_spec = self.get_class_spec(state_class,frontend_sys_spec)
                if class_spec != None:
                    context = tree +"\n"+class_spec
                else:
                    logger.warning(f"Warning! Using full history for {todo}")
                    context = self._rc.history
                code, prompt = await WriteFlutterStateClassCode().run(context=context, filename=todo)

            elif "/controller/" in todo:
                ## controller class
                state_class = todo_file_name
                class_spec = self.get_class_spec(state_class,frontend_sys_spec)
                if class_spec != None:
                    context = tree +"\n"+class_spec
                else:
                    logger.warning(f"Warning! Using full history for {todo}")
                    context = self._rc.history
                code, prompt = await WriteFlutterStateClassCode().run(context=context, filename=todo)

            elif "/screens/" in todo:
                # screen_class = Path(todo).name
                # class_spec = self.get_class_spec(state_class,frontend_sys_spec)
                # if class_spec != None:
                context = frontend_sys_spec
                # else:
                #     logger.warning(f"Warning! Using full history for {todo}")
                #     context = self._rc.history
                code, prompt = await WriteFlutterScreenClassCode().run(context=context, filename=todo)

            else:
                logger.warning(f"Warning! Using Generic Flutter Code writing for {todo}")
                context = frontend_sys_spec#self._rc.history
                code, prompt = await WriteFlutterCode().run(context=context, filename=todo)
            
            logger.info(todo)
            #logger.info(code)

            if self.use_code_review:
                try:
                    rewrite_code = await WriteFlutterCodeReview().run(context=context,initial_prompt=prompt, filename=todo, code=code)
                    code = rewrite_code
                except Exception as e:
                    logger.error("code review failed!", e)
                    pass

            file_path = self.write_file(todo, code)
            msg = Message(content=code, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

            logger.info(f"Done {todo} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="QaEngineer"
        )
        return msg

    # async def _act_sp_precision(self) -> Message:
    #     code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
    #     for todo in self.todos:
    #         """
    #         # Select essential information from the historical data to reduce the length of the prompt (summarized from human experience):
    #         1. All from Architect
    #         2. All from ProjectManager
    #         3. Do we need other codes (currently needed)?
    #         TODO: The goal is not to need it. After clear task decomposition, based on the design idea, you should be able to write a single file without needing other codes. If you can't, it means you need a clearer definition. This is the key to writing longer code.
    #         """
    #         context = []
    #         msg = self._rc.memory.get_by_actions([WriteFlutterDesign, WriteFlutterFrontendDesign, WriteFlutterTasks, WriteFlutterCode])
    #         for m in msg:
    #             context.append(m.content)
    #         context_str = "\n".join(context)
    #         # Write code
    #         code = await WriteFlutterCode().run(context=context_str, filename=todo)
    #         # Code review
    #         if self.use_code_review:
    #             try:
    #                 rewrite_code = await WriteFlutterCodeReview().run(context=context_str, code=code, filename=todo)
    #                 code = rewrite_code
    #             except Exception as e:
    #                 logger.error("code review failed!", e)
    #                 pass
    #         file_path = self.write_file(todo, code)
    #         msg = Message(content=code, role=self.profile, cause_by=WriteCode)
    #         self._rc.memory.add(msg)

    #         code_msg = todo + FILENAME_CODE_SEP + str(file_path)
    #         code_msg_all.append(code_msg)

    #     logger.info(f"Done {self.get_workspace()} generating.")
    #     msg = Message(
    #         content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="FlutterQaEngineer"
    #     )
    #     return msg

    async def _act(self) -> Message:
        """Determines the mode of action based on whether code review is used."""
        # if self.use_code_review:
        #     return await self._act_sp_precision()
        return await self._act_sp()
