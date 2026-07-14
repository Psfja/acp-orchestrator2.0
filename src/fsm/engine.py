import asyncio
import json
import os
import re
import time
from src.agents.adapters.real import _extract_text
from src.fsm.states import OrchestrationState, VALID_TRANSITIONS
from src.tasks.models import Task
from src.tasks.queue import TaskQueue
from src.agents.manager import AgentManager
from src.config.loader import OrchestratorConfig
from src.fsm.context import rebuild_context
from src.logger.logger import Logger


class OrchestrationFSM:

    def __init__(
        self,
        config: OrchestratorConfig,
        manager: AgentManager,
        logger: Logger,
    ):
        self.config = config
        self.manager = manager
        self.logger = logger
        self.state = OrchestrationState.IDLE
        self.iteration = 0
        self.task_queue = TaskQueue()

    def _transition(self, new_state: OrchestrationState) -> None:
        allowed = VALID_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(f"非法状态转换: {self.state.value} -> {new_state.value}")
        old = self.state
        self.state = new_state
        self.logger.log_state(old.value, new_state.value, self.iteration or 1)

    def _parse_tasks(self, text: str) -> list[Task]:
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        json_str = json_match.group(1) if json_match else text

        arr_match = re.search(r'\[[\s\S]*\]', json_str)
        if arr_match:
            json_str = arr_match.group(0)

        try:
            raw_tasks = json.loads(json_str)
            if not isinstance(raw_tasks, list):
                return []
            tasks = []
            for t in raw_tasks:
                if isinstance(t, dict) and "id" in t and "description" in t and "assigned_agent" in t:
                    tasks.append(Task(
                        id=t["id"],
                        description=t["description"],
                        assigned_agent=t["assigned_agent"],
                        deps=t.get("deps", []),
                    ))
            return tasks
        except (json.JSONDecodeError, TypeError):
            return []

    async def _orchestrate(self, requirement: str, fail_context: str = "") -> list[Task]:
        orch_config = self.config.agents.get("orchestrator")
        if orch_config is None:
            raise ValueError("agents.yaml中缺少orchestrator配置")

        session = await self.manager.spawn("orchestrator", orch_config, timeout=self.config.settings.task_timeout_seconds)

        context = fail_context if fail_context else f"需求: {requirement}"

        self.logger.log_orch(f"接收需求: {requirement[:80]}...")
        full_response = ""

        async for update in self.manager.send_task(session, context):
            content = update.get("content", "")
            if content:
                self.logger.log_orch(content)
                full_response += content

        await self.manager.kill(session)

        tasks = self._parse_tasks(full_response)
        if not tasks:
            self.logger.log_error("编排Agent输出无法解析")
            return []

        self.logger.log_orch(f"拆分结果: {len(tasks)}个任务")
        for task in tasks:
            self.logger.log_router(f"  - {task.id} -> {task.assigned_agent}")

        return tasks

    def _save_output(self, task_id: str, content: str) -> None:
        os.makedirs("output", exist_ok=True)
        filename = f"output/{task_id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

    async def _dispatch(self, tasks: list[Task]) -> None:
        self._transition(OrchestrationState.DISPATCHING)
        self.task_queue.clear()
        self.task_queue.enqueue(tasks)

    async def _execute(self) -> None:
        self._transition(OrchestrationState.EXECUTING)

        async def execute_one(task: Task):
            agent_config = self.config.agents.get(task.assigned_agent)
            if agent_config is None:
                await self.task_queue.mark_failed(task.id, f"未知Agent: {task.assigned_agent}")
                return

            await self.task_queue.mark_running(task.id)
            timeout = self.config.settings.task_timeout_seconds
            session = await self.manager.spawn(f"exec-{task.id}", agent_config, timeout=timeout)
            self.logger.log_router(f"任务 {task.id} -> {agent_config.name}")

            try:
                full_response = ""
                updates = self.manager.send_task(session, task.description)
                async for update in updates:
                    content = update.get("content", "")
                    if content:
                        text = _extract_text(content)
                        self.logger.log_exec(agent_config.name, text)
                        full_response += text

                await self.task_queue.mark_done(task.id, full_response.strip())
                self._save_output(task.id, full_response.strip())
                self.logger.log_exec(agent_config.name, f"OK {task.id} 完成")
            except Exception as e:
                await self.task_queue.mark_failed(task.id, str(e))
                self.logger.log_error(f"{task.id} 失败: {e}")
            finally:
                await self.manager.kill(session)

            done = len(self.task_queue.get_done_tasks()) + len(self.task_queue.get_failed_tasks())
            self.logger.log_progress(done, len(self.task_queue._tasks), self.iteration)

        ready = self.task_queue.get_ready()
        while ready:
            await asyncio.gather(*[execute_one(t) for t in ready])
            ready = self.task_queue.get_ready()

    async def _review(self) -> bool:
        self._transition(OrchestrationState.REVIEWING)

        done_tasks = self.task_queue.get_done_tasks()
        review_text = "请审核以下任务产出:\n\n"
        for task in done_tasks:
            review_text += f"## {task.id}: {task.description}\n{task.result}\n\n"

        checker_config = self.config.agents.get("checker")
        if checker_config is None:
            self.logger.log_check("无检查Agent配置，跳过审核")
            return True

        session = await self.manager.spawn("checker", checker_config)
        full_response = ""

        async for update in self.manager.send_task(session, review_text):
            content = update.get("content", "")
            if content:
                self.logger.log_check(content)
                full_response += content

        await self.manager.kill(session)

        # 检查是否明确标记为"审核通过"
        passed = "审核通过" in full_response
        if not passed:
            self.logger.log_check("WARN 审核不通过")
        return passed

    async def _test(self) -> bool:
        self._transition(OrchestrationState.TESTING)

        done_tasks = self.task_queue.get_done_tasks()
        test_text = "请测试以下代码产出:\n\n"
        for task in done_tasks:
            test_text += f"## {task.id}: {task.description}\n{task.result}\n\n"

        tester_config = self.config.agents.get("tester")
        if tester_config is None:
            self.logger.log_test("无测试Agent配置，跳过测试")
            return True

        session = await self.manager.spawn("tester", tester_config)
        full_response = ""

        async for update in self.manager.send_task(session, test_text):
            content = update.get("content", "")
            if content:
                self.logger.log_test(content)
                full_response += content

        await self.manager.kill(session)

        # 检查是否明确标记为"测试通过"
        passed = "测试通过" in full_response
        if not passed:
            self.logger.log_test("FAIL 测试不通过")
        return passed

    async def run(self, requirement: str) -> dict:
        start_time = time.time()

        try:
            self._transition(OrchestrationState.ORCHESTRATING)
            self.iteration += 1

            tasks = await self._orchestrate(requirement)
            if not tasks:
                self._transition(OrchestrationState.FAILED)
                return {"status": "failed", "reason": "编排Agent输出解析失败"}

            while self.iteration <= self.config.settings.max_iterations:
                await self._dispatch(tasks)
                await self._execute()

                if self.task_queue.has_failed():
                    done = self.task_queue.get_done_tasks()
                    failed = self.task_queue.get_failed_tasks()
                    fail_info = "以下任务执行失败:\n"
                    for t in failed:
                        fail_info += f"- FAIL {t.id}: {t.error}\n"

                    context = rebuild_context(requirement, done, fail_info, self.iteration)
                    self.logger.log_error(f"返工: 第{self.iteration}轮有失败任务")
                    tasks = await self._orchestrate(requirement, fail_context=context)
                    if not tasks:
                        self._transition(OrchestrationState.FAILED)
                        return {"status": "failed", "reason": "编排Agent返工解析失败"}
                    continue

                review_ok = await self._review()
                if not review_ok:
                    done = self.task_queue.get_done_tasks()
                    fail_info = "检查不通过: 代码存在问题需要修复"
                    context = rebuild_context(requirement, done, fail_info, self.iteration)
                    tasks = await self._orchestrate(requirement, fail_context=context)
                    if not tasks:
                        self._transition(OrchestrationState.FAILED)
                        return {"status": "failed", "reason": "编排Agent返工解析失败"}
                    continue

                test_ok = await self._test()
                if not test_ok:
                    done = self.task_queue.get_done_tasks()
                    fail_info = "测试不通过: 部分测试用例失败"
                    context = rebuild_context(requirement, done, fail_info, self.iteration)
                    tasks = await self._orchestrate(requirement, fail_context=context)
                    if not tasks:
                        self._transition(OrchestrationState.FAILED)
                        return {"status": "failed", "reason": "编排Agent返工解析失败"}
                    continue

                # 全部通过
                self._transition(OrchestrationState.COMPLETED)
                elapsed = f"{time.time() - start_time:.2f}秒"
                total_tasks_done = len(self.task_queue.get_done_tasks())
                self.logger.log_completed(self.iteration, total_tasks_done, elapsed)
                return {
                    "status": "completed",
                    "iterations": self.iteration,
                    "total_tasks": total_tasks_done,
                    "elapsed": elapsed,
                }

            # 超出最大迭代次数
            self._transition(OrchestrationState.FAILED)
            return {"status": "failed", "reason": f"超过最大迭代次数({self.config.settings.max_iterations})"}

        except Exception as e:
            self._transition(OrchestrationState.FAILED)
            self.logger.log_failed(str(e))
            return {"status": "failed", "reason": str(e)}
