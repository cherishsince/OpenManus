# tool/planning.py
from typing import Dict, List, Literal, Optional

from app.exceptions import ToolError
from app.tool.base import BaseTool, ToolResult


_PLANNING_TOOL_DESCRIPTION = """
规划工具：允许代理创建和管理复杂任务的执行计划。
提供创建计划、更新计划步骤和跟踪进度的功能。

A planning tool that allows the agent to create and manage plans for solving complex tasks.
The tool provides functionality for creating plans, updating plan steps, and tracking progress.
"""


class PlanningTool(BaseTool):
    """
    规划工具类：允许代理创建和管理复杂任务的执行计划
    提供创建计划、更新计划步骤和跟踪进度的功能
    
    A planning tool that allows the agent to create and manage plans for solving complex tasks.
    The tool provides functionality for creating plans, updating plan steps, and tracking progress.
    """

    name: str = "planning"  # 工具名称
    description: str = _PLANNING_TOOL_DESCRIPTION  # 工具描述
    parameters: dict = {  # 工具参数定义
        "type": "object",
        "properties": {
            "command": {
                "description": "要执行的命令。可用命令：create, update, list, get, set_active, mark_step, delete",
                "enum": [
                    "create",  # 创建计划
                    "update",  # 更新计划
                    "list",    # 列出所有计划
                    "get",     # 获取计划详情
                    "set_active",  # 设置活动计划
                    "mark_step",   # 标记步骤状态
                    "delete",      # 删除计划
                ],
                "type": "string",
            },
            "plan_id": {
                "description": "计划的唯一标识符。create、update、set_active和delete命令必需；get和mark_step可选（未指定时使用活动计划）",
                "type": "string",
            },
            "title": {
                "description": "计划标题。create命令必需，update命令可选",
                "type": "string",
            },
            "steps": {
                "description": "计划步骤列表。create命令必需，update命令可选",
                "type": "array",
                "items": {"type": "string"},
            },
            "step_index": {
                "description": "要更新的步骤索引（从0开始）。mark_step命令必需",
                "type": "integer",
            },
            "step_status": {
                "description": "设置步骤的状态。用于mark_step命令",
                "enum": ["not_started", "in_progress", "completed", "blocked"],
                "type": "string",
            },
            "step_notes": {
                "description": "步骤的附加说明。mark_step命令可选",
                "type": "string",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    plans: dict = {}  # 存储计划的字典，以plan_id为键
    _current_plan_id: Optional[str] = None  # 当前活动计划的ID

    async def execute(
        self,
        *,
        command: Literal[
            "create", "update", "list", "get", "set_active", "mark_step", "delete"
        ],
        plan_id: Optional[str] = None,
        title: Optional[str] = None,
        steps: Optional[List[str]] = None,
        step_index: Optional[int] = None,
        step_status: Optional[
            Literal["not_started", "in_progress", "completed", "blocked"]
        ] = None,
        step_notes: Optional[str] = None,
        **kwargs,
    ):
        """
        执行规划工具的指定命令

        参数:
        - command: 要执行的操作
        - plan_id: 计划的唯一标识符
        - title: 计划标题（用于create命令）
        - steps: 计划步骤列表（用于create命令）
        - step_index: 要更新的步骤索引（用于mark_step命令）
        - step_status: 设置步骤的状态（用于mark_step命令）
        - step_notes: 步骤的附加说明（用于mark_step命令）

        Execute the planning tool with the given command and parameters.

        Parameters:
        - command: The operation to perform
        - plan_id: Unique identifier for the plan
        - title: Title for the plan (used with create command)
        - steps: List of steps for the plan (used with create command)
        - step_index: Index of the step to update (used with mark_step command)
        - step_status: Status to set for a step (used with mark_step command)
        - step_notes: Additional notes for a step (used with mark_step command)
        """

        if command == "create":
            return self._create_plan(plan_id, title, steps)
        elif command == "update":
            return self._update_plan(plan_id, title, steps)
        elif command == "list":
            return self._list_plans()
        elif command == "get":
            return self._get_plan(plan_id)
        elif command == "set_active":
            return self._set_active_plan(plan_id)
        elif command == "mark_step":
            return self._mark_step(plan_id, step_index, step_status, step_notes)
        elif command == "delete":
            return self._delete_plan(plan_id)
        else:
            raise ToolError(
                f"未识别的命令：{command}。允许的命令有：create, update, list, get, set_active, mark_step, delete"
            )

    def _create_plan(
        self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]
    ) -> ToolResult:
        """
        创建新的执行计划
        
        参数:
        - plan_id: 计划ID
        - title: 计划标题
        - steps: 计划步骤列表
        
        返回:
            ToolResult: 包含创建结果的工具结果对象
            
        Create a new execution plan.
        """
        if not plan_id:
            raise ToolError("创建计划命令需要plan_id参数")
        if not title:
            raise ToolError("创建计划命令需要title参数")
        if not steps:
            raise ToolError("创建计划命令需要steps参数")

        if plan_id in self.plans:
            raise ToolError(f"已存在ID为{plan_id}的计划")

        plan = {
            "plan_id": plan_id,
            "title": title,
            "steps": steps,
            "step_statuses": ["not_started"] * len(steps),
            "step_notes": [""] * len(steps),
        }
        self.plans[plan_id] = plan
        self._current_plan_id = plan_id

        return ToolResult(
            output=f"已创建计划'{title}'（ID: {plan_id}）\n\n{self._format_plan(plan)}"
        )

    def _update_plan(
        self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]
    ) -> ToolResult:
        """
        更新现有计划的标题或步骤
        
        参数:
        - plan_id: 计划ID
        - title: 新的计划标题（可选）
        - steps: 新的计划步骤列表（可选）
        
        返回:
            ToolResult: 包含更新结果的工具结果对象
            
        Update an existing plan's title or steps.
        """
        if not plan_id:
            raise ToolError("更新计划命令需要plan_id参数")

        if plan_id not in self.plans:
            raise ToolError(f"未找到ID为{plan_id}的计划")

        plan = self.plans[plan_id]
        if title:
            plan["title"] = title
        if steps:
            old_len = len(plan["steps"])
            plan["steps"] = steps
            new_len = len(steps)
            if new_len > old_len:
                # 如果新步骤更多，为新步骤添加默认状态和说明
                plan["step_statuses"].extend(["not_started"] * (new_len - old_len))
                plan["step_notes"].extend([""] * (new_len - old_len))
            elif new_len < old_len:
                # 如果新步骤更少，截断状态和说明列表
                plan["step_statuses"] = plan["step_statuses"][:new_len]
                plan["step_notes"] = plan["step_notes"][:new_len]

        return ToolResult(
            output=f"已更新计划'{plan['title']}'（ID: {plan_id}）\n\n{self._format_plan(plan)}"
        )

    def _list_plans(self) -> ToolResult:
        """
        列出所有计划的摘要信息
        
        返回:
            ToolResult: 包含计划列表的工具结果对象
            
        List all plans with summary information.
        """
        if not self.plans:
            return ToolResult(output="当前没有任何计划")

        output = ["当前计划列表："]
        for plan in self.plans.values():
            completed = sum(1 for status in plan["step_statuses"] if status == "completed")
            total = len(plan["steps"])
            status = "（当前活动计划）" if plan["plan_id"] == self._current_plan_id else ""
            output.append(
                f"- {plan['title']} (ID: {plan['plan_id']}) - 进度：{completed}/{total}{status}"
            )

        return ToolResult(output="\n".join(output))

    def _get_plan(self, plan_id: Optional[str]) -> ToolResult:
        """
        获取计划的详细信息
        
        参数:
        - plan_id: 计划ID（可选，未指定时使用当前活动计划）
        
        返回:
            ToolResult: 包含计划详情的工具结果对象
            
        Get detailed information about a plan.
        """
        if not plan_id:
            if not self._current_plan_id:
                raise ToolError(
                    "没有活动计划。请指定plan_id或设置活动计划。"
                )
            plan_id = self._current_plan_id

        if plan_id not in self.plans:
            raise ToolError(f"未找到ID为{plan_id}的计划")

        plan = self.plans[plan_id]
        return ToolResult(output=self._format_plan(plan))

    def _set_active_plan(self, plan_id: Optional[str]) -> ToolResult:
        """
        设置活动计划
        
        参数:
        - plan_id: 要设置为活动计划的计划ID
        
        返回:
            ToolResult: 包含设置结果的工具结果对象
            
        Set a plan as the active plan.
        """
        if not plan_id:
            raise ToolError("设置活动计划命令需要plan_id参数")

        if plan_id not in self.plans:
            raise ToolError(f"未找到ID为{plan_id}的计划")

        self._current_plan_id = plan_id
        plan = self.plans[plan_id]
        return ToolResult(
            output=f"已将计划'{plan['title']}'（ID: {plan_id}）设置为活动计划\n\n{self._format_plan(plan)}"
        )

    def _mark_step(
        self,
        plan_id: Optional[str],
        step_index: Optional[int],
        step_status: Optional[str],
        step_notes: Optional[str],
    ) -> ToolResult:
        """
        标记计划步骤的状态和说明
        
        参数:
        - plan_id: 计划ID（可选，未指定时使用当前活动计划）
        - step_index: 步骤索引
        - step_status: 步骤状态
        - step_notes: 步骤说明
        
        返回:
            ToolResult: 包含更新结果的工具结果对象
            
        Mark a step's status and add notes.
        """
        if not plan_id:
            if not self._current_plan_id:
                raise ToolError(
                    "没有活动计划。请指定plan_id或设置活动计划。"
                )
            plan_id = self._current_plan_id

        if plan_id not in self.plans:
            raise ToolError(f"未找到ID为{plan_id}的计划")

        if step_index is None:
            raise ToolError("标记步骤命令需要step_index参数")

        plan = self.plans[plan_id]
        if step_index < 0 or step_index >= len(plan["steps"]):
            raise ToolError(f"步骤索引{step_index}超出范围")

        if step_status:
            plan["step_statuses"][step_index] = step_status
        if step_notes:
            plan["step_notes"][step_index] = step_notes

        return ToolResult(
            output=f"已更新计划'{plan['title']}'的步骤{step_index}\n\n{self._format_plan(plan)}"
        )

    def _delete_plan(self, plan_id: Optional[str]) -> ToolResult:
        """
        删除指定的计划
        
        参数:
        - plan_id: 要删除的计划ID
        
        返回:
            ToolResult: 包含删除结果的工具结果对象
            
        Delete a specified plan.
        """
        if not plan_id:
            raise ToolError("删除计划命令需要plan_id参数")

        if plan_id not in self.plans:
            raise ToolError(f"未找到ID为{plan_id}的计划")

        plan = self.plans.pop(plan_id)
        if plan_id == self._current_plan_id:
            self._current_plan_id = None

        return ToolResult(output=f"已删除计划'{plan['title']}'（ID: {plan_id}）")

    def _format_plan(self, plan: Dict) -> str:
        """
        格式化计划信息为可读字符串
        
        参数:
        - plan: 计划字典
        
        返回:
            str: 格式化后的计划信息
            
        Format a plan as a readable string.
        """
        # 计划标题和ID
        output = [f"计划：{plan['title']} (ID: {plan['plan_id']})"]
        if plan["plan_id"] == self._current_plan_id:
            output.append("状态：当前活动计划")

        # 进度统计
        completed = sum(1 for status in plan["step_statuses"] if status == "completed")
        total = len(plan["steps"])
        output.append(f"进度：已完成 {completed}/{total} 个步骤")

        # 步骤详情
        output.append("\n步骤：")
        for i, (step, status, notes) in enumerate(
            zip(plan["steps"], plan["step_statuses"], plan["step_notes"])
        ):
            status_map = {
                "not_started": "未开始",
                "in_progress": "进行中",
                "completed": "已完成",
                "blocked": "已阻塞",
            }
            status_str = status_map.get(status, status)
            step_line = f"{i}. {step} [{status_str}]"
            if notes:
                step_line += f"\n   说明：{notes}"
            output.append(step_line)

        return "\n".join(output)
