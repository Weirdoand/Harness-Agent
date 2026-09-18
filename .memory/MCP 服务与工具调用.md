---
name: MCP 服务与工具调用
type: 项目事实
description: docs/deploy 均为本地 mock；工具命名 mcp__<server>__<tool>；connect_mcp 重复连接幂等。
---

MCP 工具按 mcp__<server>__<tool> 形式注册和调用，例如 mcp__docs__search(query='agent loop')。新的 MCP 服务连接成功后会打印已注册工具列表。docs server 是本地 mock（_mock_server_docs），其 list_tools 仅返回 docs_search（调用形式 mcp__docs__search，参数 query）。不存在 docs_get_version / get_version 工具，在 llm_chat.py 中检索 get_version / getVersion 也无任何匹配，因此不要尝试调用 docs_get_version。docs_search 目前返回模拟结果（如 {'server': 'docs', 'query': 'agent hooks', 'result': '模拟文档检索结果：agent hooks'}），不是真实文档内容，不能作为权威资料引用。在 llm_chat.py 中，MCP_SERVERS 注册表当前定义为 MCP_SERVERS = dict(MOCK_SERVERS)，docs 服务由本地函数 _mock_server_docs 实现并通过 MCP_SERVERS 注册。调用 connect_mcp(name='docs') 时，若该 server 此前已注册连接，会返回「MCP docs 已经连接，无需重复注册」，不会报错也不会重复注册；重复调用是安全幂等的，但通常没有必要在每次对话开头重复执行。deploy server 也已连接，是本地 mock（_mock_server_deploy），仅注册工具 deploy_preview；没有 status/get_status/list_services 等查询工具。deploy_preview 会生成模拟部署结果（返回 {'server': 'deploy', 'service': ..., 'environment': ..., 'status': 'simulated'}），属于部署动作。