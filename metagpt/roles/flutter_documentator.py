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
import os
import traceback

from metagpt.actions import WriteCode, WriteCodeReview, WriteDesign, WriteTasks
from metagpt.actions.add_requirement import BossRequirement
from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.actions.flutter_frontend_design_api import WriteFlutterFrontendDesign
from metagpt.actions.flutter_project_explorer import WriteFlutterExploration
from metagpt.actions.flutter_project_management import WriteFlutterTasks
from metagpt.actions.write_flutter_code import WriteFlutterCode
from metagpt.actions.write_flutter_code_fix import WriteFlutterCodeFix
from metagpt.actions.write_flutter_code_fix_tasks import WriteFlutterCodeFixTasks
from metagpt.actions.write_flutter_code_review import WriteFlutterCodeReview
from metagpt.actions.write_flutter_data_class_code import WriteFlutterDataClassCode
from metagpt.actions.write_flutter_dependencies import WriteFlutterDependencies
from metagpt.actions.write_flutter_documentation import WriteFlutterDocumentation
from metagpt.actions.write_flutter_repository_class_code import WriteFlutterRepositoryClassCode
from metagpt.actions.write_flutter_screen_class_code import WriteFlutterScreenClassCode
from metagpt.actions.write_flutter_state_class_code import WriteFlutterStateClassCode
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from metagpt.utils.special_tokens import FILENAME_CODE_SEP, MSG_SEP
from metagpt.flutter_common import get_context, get_workspace, get_workspace_name, to_camel_case
import re
import subprocess



class FlutterDocumentator(Role):
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
        name: str = "Chris",
        profile: str = "FlutterDocumentator",
        goal: str = "Write elegant, readable, extensible, efficient Documentation",
        constraints: str = "The code should conform to standards and be modular and maintainable",
        n_borg: int = 1,
        use_code_review: bool = False,
    ) -> None:
        """Initializes the Engineer role with given attributes."""
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteFlutterDocumentation])
        self.use_code_review = use_code_review
        if self.use_code_review:
            self._init_actions([WriteFlutterDocumentation, WriteFlutterCodeReview])
        self._watch([BossRequirement])
        self.n_borg = n_borg

    @classmethod
    def parse_tasks(self, task_msg: str) -> list[str]:
        # Regular expression to extract tasks
        pattern = re.compile(r'(?P<description>^.+?)\n\s+- File: (?P<file>.+?)\n\s+- Operation: (?P<operation>.+?)\n', re.MULTILINE)

        matches = pattern.findall(task_msg)

        # Creating a list of dictionaries based on the extracted tasks
        tasks = [{'file_path': match[1], 'description': match[0].strip(), 'operation': match[2]} for match in matches]

        # Removing the task number from the description
        for task in tasks:
            task['number'] = int(task['description'].split(".")[0])
            task['checked'] = "[x]" in task['description']
            task['description'] = re.sub(r'^\d+\.\s*', '', task['description'].replace('[x]', '').replace('[ ]', '').strip())
        

        return tasks

        #if task_msg.instruct_content:
        #    return task_msg.instruct_content.dict().get("Task list")
        #return CodeParser.parse_file_list(block="Task list", text=task_msg.content)

    @classmethod
    def parse_code(self, code_text: str) -> str:
        return CodeParser.parse_code(block="", text=code_text)

    # @classmethod
    # def parse_workspace(cls, system_design_msg: Message) -> str:
    #     if system_design_msg.instruct_content:
    #         return system_design_msg.instruct_content.dict().get("Flutter package name").strip().strip("'").strip('"')
    #     return CodeParser.parse_str(block="Flutter package name", text=system_design_msg.content)

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


    def read_file(self,filename):
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

    async def _act_sp(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        ws = get_workspace(self)

        tasks_file = ws / "docs" / "tasks.md"
        todos = self.read_file(tasks_file)

        todos = self.parse_tasks(todos)

        context = "\n".join(code_msg_all) #get_context(self)

        for todo in todos:
            logger.info(f"Processing: {todo}")
            file_path = "lib/"+todo["file_path"]
            operation = todo["operation"]
            description = todo["description"]
            number =  todo["number"]
            checked = todo["checked"]

            if checked:
                continue

            code = ""

            try:
                logger.info(f"Processing: {file_path}")
                code = self.read_file(ws/file_path)
                logger.info(f"Code: {code}")
            except:
                pass

            ### context...
            code, prompt = await WriteFlutterDocumentation().run(context=context, code=code, filename=file_path)
            #code, prompt = await globals()[operation]().run(context=task_context, code=code, filename=file_path)

            subprocess.run(["flutter","pub", "get",ws])


            # if self.use_code_review:
            #     errors = self.fix_errors()

            #     file_errors = []

            #     for error in errors:
            #         if file_path in error["file_path"]:
            #             file_errors.append(error)

            #     context = context +"\n"+ "\n".join(str(file_errors))

            #     try:
            #         rewrite_code = await WriteFlutterCodeReview().run(context=context,initial_prompt=prompt, filename=file_path, code=code)
            #         code = rewrite_code
            #     except Exception as e:
            #         logger.error("code review failed!", e)
            #         pass

            file_path = self.write_file(file_path, code)
            msg = Message(content=code, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)

            code_msg = description + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

            ### write updated tasks list
            todos = self.read_file(tasks_file)

            todos = todos.replace(f"\n{number}. [ ]",f"\n{number}. [x]",1)

            ### set number checked
            tasks_file.write_text(todos)

            logger.info(f"Done {todo} generating.")

        msg = Message(
            content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="QaEngineer"
        )
        return msg

    def fix_errors(self):
        ws = get_workspace(self)
        error_file = ws/"errors.txt"
        try:
            subprocess.run(["flutter", "analyze",ws,"--write",error_file]) 
        except Exception as e:
            logger.error(f"Error at analyzing Project: {e}")

        ## now load errors and work on it
        # Reading the first few lines of the file to understand its structure
        with open(error_file, "r") as file:
            lines = file.readlines()


        # Define a pattern to match the error format
        pattern = r"\[(?P<error_type>[^\]]+)\] (?P<description>.+) \((?P<file_path>[^:]+):(?P<line_number>\d+):\d+\)"

        # Extract information for each error
        parsed_errors = []
        for line in lines:
            match = re.match(pattern, line)
            if match:
                parsed_errors.append(match.groupdict())

        for error in parsed_errors:
            path = error['file_path']
            workspace_index = path.find('workspace')
            if workspace_index != -1:
                error['file_path'] = path[workspace_index:]

        os.remove(error_file)

        return parsed_errors

    async def _act(self) -> Message:
        """Determines the mode of action based on whether code review is used."""
        # if self.use_code_review:
        #     return await self._act_sp_precision()
        return await self._act_sp()
