#!/usr/bin/env python
# -*- coding: utf-8 -*-


from metagpt.actions.action_output import ActionOutput
from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.actions.flutter_frontend_design_api import WriteFlutterFrontendDesign
from metagpt.actions.flutter_project_management import WriteFlutterTasks
from metagpt.actions.write_prd import WritePRD
from metagpt.roles import Role

from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.flutter_common import get_workspace
from metagpt.utils.json_to_markdown import json_to_markdown


class FlutterProjectManager(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """

    def __init__(
        self,
        name: str = "Paul",
        profile: str = "Flutter Project Manager",
        goal: str = "Improve team efficiency and deliver with quality and quantity",
        constraints: str = "",
    ) -> None:
        """
        Initializes the ProjectManager role with given attributes.

        Args:
            name (str): Name of the project manager.
            profile (str): Role profile.
            goal (str): Goal of the project manager.
            constraints (str): Constraints or limitations for the project manager.
        """
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteFlutterTasks])
        self._watch([WriteFlutterFrontendDesign])

    def _save(self, ws, context, rsp):

        file_path = ws / "docs/api_spec_and_tasks.md"
        file_path.write_text(json_to_markdown(rsp.instruct_content.dict()))
        logger.info(f"Saved tasks to: {file_path}")


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

        self._save(ws,context,msg)

        return msg