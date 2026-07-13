import argparse
import asyncio
import os
import sys
from src.config.loader import load_config
from src.fsm.engine import OrchestrationFSM
from src.agents.manager import AgentManager
from src.agents.adapters.mock import MockAdapter
from src.logger.logger import Logger


def get_default_config_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "agents.yaml")


async def main_async(requirement: str, config_path: str) -> int:
    logger = Logger()

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        logger.log_error(f"配置文件不存在: {config_path}")
        return 1

    manager = AgentManager(logger=logger)

    manager.register_adapter("mock", MockAdapter)
    manager.register_adapter("claude_code", MockAdapter)
    manager.register_adapter("codex", MockAdapter)
    manager.register_adapter("gemini", MockAdapter)
    manager.register_adapter("echo", MockAdapter)

    fsm = OrchestrationFSM(config=config, manager=manager, logger=logger)
    result = await fsm.run(requirement)

    if result["status"] == "completed":
        print(f"\n{'='*50}")
        print(f"状态: 完成")
        print(f"迭代: {result['iterations']}轮")
        print(f"任务: {result['total_tasks']}个")
        print(f"耗时: {result['elapsed']}")
        return 0
    else:
        print(f"\n{'='*50}")
        print(f"状态: 失败")
        print(f"原因: {result['reason']}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="ACP Orchestrator - 多Agent编排框架",
    )
    parser.add_argument(
        "requirement",
        nargs="?",
        help="需求描述 (如: '开发一个登录页面')",
    )
    parser.add_argument(
        "-c", "--config",
        default=get_default_config_path(),
        help="配置文件路径 (默认: agents.yaml)",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="检查配置文件是否合法",
    )

    args = parser.parse_args()

    if args.check_config:
        try:
            config = load_config(args.config)
            print(f"配置文件: {args.config}")
            print(f"Agent数量: {len(config.agents)}")
            for key, agent in config.agents.items():
                print(f"  - {key}: {agent.name} ({agent.role}) [{agent.adapter}]")
            print("配置合法。")
            return 0
        except Exception as e:
            print(f"配置错误: {e}")
            return 1

    if not args.requirement:
        parser.print_help()
        return 1

    return asyncio.run(main_async(args.requirement, args.config))


if __name__ == "__main__":
    sys.exit(main())
