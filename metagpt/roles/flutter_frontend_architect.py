#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""

from pathlib import Path
from metagpt.const import WORKSPACE_ROOT
import shutil

from metagpt.actions import WritePRD
from metagpt.actions.action_output import ActionOutput
from metagpt.actions.flutter_frontend_design_api import WriteFlutterFrontendDesign
from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.roles import Role
from metagpt.roles.product_manager import get_workspace
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.common import CodeParser
from metagpt.utils.mermaid import mermaid_to_file


class FlutterFrontendArchitect(Role):
    """
    Represents an Architect role in a software development process.

    Attributes:
        name (str): Name of the architect.
        profile (str): Role profile, default is 'Architect'.
        goal (str): Primary goal or responsibility of the architect.
        constraints (str): Constraints or guidelines for the architect.
    """

    def __init__(
        self,
        name: str = "Daniel",
        profile: str = "Flutter Frontend Architect",
        goal: str = "Design a concise, usable, modular, complete flutter frontend based system",
        constraints: str = "Try to specify good open source tools as much as possible. Use Riverpod as the state management library.",
    ) -> None:
        """Initializes the Architect with given attributes."""
        super().__init__(name, profile, goal, constraints)

        # Initialize actions specific to the Architect role
        self._init_actions([WriteFlutterFrontendDesign])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WriteFlutterDesign})


    async def _save_system_design(self, docs_path, resources_path, system_design):
        data_classes = system_design.instruct_content.dict()[
            "State classes"
        ]  # CodeParser.parse_code(block="Data structures and interface definitions", text=content)
        repository_classes = system_design.instruct_content.dict()[
            "Device API classes"
        ]  # CodeParser.parse_code(block="Program call flow", text=content)
        await mermaid_to_file(data_classes, resources_path / "state_classes")
        await mermaid_to_file(repository_classes, resources_path / "device_api_classes")
        system_design_file = docs_path / "frontend_system_design.md"
        logger.info(f"Saving System Designs to {system_design_file}")
        system_design_file.write_text((json_to_markdown(system_design.instruct_content.dict())))

    async def _save(self,workspace, context, system_design):
        logger.info("Saving Frontend Design")
        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_system_design(docs_path, resources_path, system_design)

    async def _act(self) -> Message:

        logger.info(f"{self._setting}: ready to {self._rc.todo}")

        context = self._rc.important_memory
        response = await self._rc.todo.run(context)
        
        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                        role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)

        ws = get_workspace(self)  
        logger.info(f"Workspace: {ws}")

        await self._save(ws,context,msg)

        return msg