#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from metagpt.actions import BossRequirement, WritePRD
from metagpt.roles import Role
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.actions.action_output import ActionOutput
import subprocess
from metagpt.flutter_common import get_workspace
from metagpt.const import WORKSPACE_ROOT

class ProductManager(Role):
    """
    Represents a Product Manager role responsible for product development and management.

    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
    """

    def __init__(
        self,
        name: str = "Alice",
        profile: str = "Product Manager",
        goal: str = "Efficiently create a successful product",
        constraints: str = "",
    ) -> None:
        """
        Initializes the ProductManager role with given attributes.

        Args:
            name (str): Name of the product manager.
            profile (str): Role profile.
            goal (str): Goal of the product manager.
            constraints (str): Constraints or limitations for the product manager.
        """
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WritePRD])
        self._watch([BossRequirement])




    ### save files
    async def _save_prd(self, docs_path, resources_path, msg):
        prd_file = docs_path / "prd.md"
        if msg.instruct_content and msg.instruct_content.dict()["Competitive Quadrant Chart"]:
            quadrant_chart = msg.instruct_content.dict()["Competitive Quadrant Chart"]
            if False:
                await mermaid_to_file(quadrant_chart, resources_path / "competitive_analysis")

        if msg.instruct_content:
            try:
                logger.info(f"Saving PRD to {prd_file}")
                prd_file.write_text(json_to_markdown(msg.instruct_content.dict()))
            except Exception as e:
                logger.error(f"Error at saving PRD: {e}")


    async def _create_project(self):
        ws = get_workspace(self)        
        try:
            subprocess.run(["flutter", "create",ws]) 

            packages_path = ws / "packages"
            packages_path.mkdir(parents=True, exist_ok=True)

            core_path = packages_path / "float_core"
            apis_path = packages_path / "float_apis"

            core_path.mkdir(parents=True, exist_ok=True)
            apis_path.mkdir(parents=True, exist_ok=True)

            subprocess.run(["git", "clone","https://github.com/appBizniz/float_core.git",core_path]) 
            subprocess.run(["git", "clone","https://github.com/appBizniz/float_apis.git",apis_path]) 

            subprocess.run(["flutter","pub", "get",ws])


            subprocess.run(["flutter","pub", "get",core_path])
            subprocess.run(["flutter","pub", "get",apis_path])


            subprocess.run(["flutter","pub", "get",ws])


        except Exception as e:
            logger.error(f"Error at creating Project: {e}")



    async def _save(self,workspace, context, msg):
        await self._create_project()


        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_prd(docs_path, resources_path, msg)






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
    

