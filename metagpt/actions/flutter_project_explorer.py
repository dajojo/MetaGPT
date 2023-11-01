#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
"""
from typing import List

import re
import os

from metagpt.actions.action import Action
from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.logs import logger
from metagpt.schema import Message


class WriteFlutterExploration(Action):
    def __init__(self, name="WriteFlutterExploration", context=None, llm=None):
        super().__init__(name, context, llm)


    def explore_folder(self,path, indent=0):
        if not os.path.exists(path):
            return "Path does not exist!"
        
        markdown = ""
        if os.path.isdir(path):
            for item in sorted(os.listdir(path)):
                # Skip items that start with a dot
                if item.startswith('.'):
                    continue
                
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    markdown += "  " * indent + f"- **{item}/**\n" + self.explore_folder(item_path, indent + 1)
                elif os.path.isfile(item_path):
                    markdown += "  " * indent + f"- {item}\n"
        else:
            return "Provided path is not a directory!"
        
        return markdown

    def run(self, folder_path, format="markdown"):
        #### now LLM involvement here...

        md = self.explore_folder(folder_path)

        print(md)

        return md


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
