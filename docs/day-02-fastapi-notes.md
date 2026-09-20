# 第 2 天：FastAPI 路由、请求参数与数据校验

## 1. 今天的学习目标

今天不是为了堆积接口数量，而是理解一条 HTTP 请求怎样进入 FastAPI，并掌握三种常见输入方式：

- 路径参数：从 URL 路径中取得一个明确对象的标识。
- 查询参数：在 URL 的 `?` 后提供筛选条件。
- 请求正文：用 JSON 提交结构化数据。
- Pydantic：在接口函数执行前验证请求正文。
- TDD：先写测试并看到它按预期失败，再写最小实现使测试通过。

## 2. HTTP 接口由什么决定

一个接口不能只看 URL，还要同时看 HTTP 方法和路径。

```text
GET  /api/v1/stocks/600519.sh   获取一只股票
GET  /api/v1/stocks?query=平安  搜索股票
POST /api/v1/watchlists         创建自选股列表
```

即使路径相同，不同 HTTP 方法也可以表示不同操作。例如，`GET` 通常读取数据，`POST` 通常创建数据。

## 3. 路径参数

路由中的 `{symbol}` 是路径参数：

```python
@application.get("/api/v1/stocks/{symbol}", tags=["stocks"])
async def get_stock(symbol: str) -> dict[str, str]:
    return {"symbol": symbol.upper()}
```

当客户端访问：

```text
GET /api/v1/stocks/600519.sh
```

FastAPI 会把 `600519.sh` 传给 `symbol`。`symbol.upper()` 把它转换成 `600519.SH`。

路径参数适合表示“具体是哪一个资源”，例如股票代码、用户 ID 或报告 ID。

## 4. 查询参数

函数参数 `query` 没有出现在路由路径里，因此 FastAPI 把它识别成查询参数：

```python
@application.get("/api/v1/stocks", tags=["stocks"])
async def search_stocks(query: str) -> list[dict[str, str]]:
    ...
```

请求示例：

```text
GET /api/v1/stocks?query=平安
```

查询参数适合搜索、筛选、排序和分页。浏览器把中文显示为 `%E5...` 是正常的 URL 编码，服务器解码后仍然得到“平安”。

## 5. 请求正文

创建自选股列表时，客户端发送 JSON：

```json
{
  "name": "核心持仓"
}
```

因为它是结构化数据，并且是在创建资源，所以使用 `POST` 和请求正文比把名称写进 URL 更合适。

## 6. Pydantic 请求模型

请求模型定义了允许接收的数据结构和校验规则：

```python
class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
```

它表达了三件事：

- 请求正文必须包含 `name`。
- `name` 必须是字符串。
- 字符串长度必须在 1 到 40 之间。

接口通过类型标注使用这个模型：

```python
async def create_watchlist(
    payload: CreateWatchlistRequest,
) -> dict[str, int | str]:
    return {
        "id": 1,
        "name": payload.name,
    }
```

请求到达后，FastAPI 先让 Pydantic 校验 JSON。校验成功时，接口得到 `payload`；校验失败时，FastAPI 直接返回 `422`，接口函数不会执行。

Pydantic 负责数据解析和校验，不负责把数据保存到数据库。目前返回的 `id = 1` 只是本阶段的最小实现。

## 7. 今天遇到的状态码

| 状态码 | 含义 | 今天的场景 |
| --- | --- | --- |
| `200 OK` | 请求成功 | 查询股票、健康检查 |
| `201 Created` | 成功创建资源 | 创建自选股列表 |
| `404 Not Found` | 没有匹配的接口或资源 | 实现接口前运行测试 |
| `422 Unprocessable Content` | 请求格式可读取，但内容不符合规则 | `name` 为空字符串 |

`404` 在 RED 阶段是有价值的信息：它证明测试真的访问了尚未实现的接口。`422` 则证明 Pydantic 的校验规则生效。

## 8. 测试如何模拟浏览器请求

测试中的关键代码：

```python
transport = httpx.ASGITransport(app=app)

async with httpx.AsyncClient(
    transport=transport,
    base_url="http://test",
) as client:
    response = await client.post(
        "/api/v1/watchlists",
        json={"name": "核心持仓"},
    )
```

- `ASGITransport(app=app)`：把测试请求直接交给 FastAPI 应用，不需要真的打开浏览器或占用网络端口。
- `AsyncClient`：异步 HTTP 客户端，用法类似真实客户端。
- `base_url="http://test"`：提供测试用的基础地址，不会访问真实网站。
- `await client.post(...)`：等待异步请求完成。
- `asyncio.run(...)`：从普通测试函数启动并运行异步函数。
- `assert`：比较实际结果和预期结果，不一致时测试失败。

自动测试和 Swagger 的请求最终进入同一个 FastAPI 应用。区别只是发送请求的客户端不同。

## 9. 一次请求的完整流程

```text
客户端发送 POST /api/v1/watchlists 和 JSON
    ↓
FastAPI 根据 HTTP 方法和路径匹配路由
    ↓
Pydantic 按 CreateWatchlistRequest 校验 JSON
    ↓
校验失败：直接返回 422
校验成功：创建 payload 并执行 create_watchlist()
    ↓
Python 字典被转换为 JSON
    ↓
返回 201 和响应正文
```

## 10. 今天使用的 TDD 流程

### RED：先证明功能不存在

先写创建成功和拒绝空名称两个测试。第一次运行时，两项都得到 `404`。这不是意外错误，而是因为路由尚未实现。

### GREEN：只写通过测试所需的最小代码

添加请求模型和 `POST /api/v1/watchlists` 后：

```text
pytest tests/test_watchlists.py -v
2 passed
```

### 回归测试：检查旧功能

继续运行全部测试：

```text
pytest -v
5 passed
```

这一步确认新功能没有破坏健康检查和股票接口。

### Swagger 手动验证

- 合法名称返回 `201` 和创建结果。
- 空名称返回 `422`，错误位置为 `body -> name`。

自动测试适合反复执行，Swagger 适合理解和演示接口，两者不能完全互相替代。

## 11. 容易混淆的地方

1. Pydantic 不是数据库。它只校验数据，程序重启后不会保留创建结果。
2. `POST`、`GET` 是请求方法；`/api/v1/watchlists` 是路径。两者共同确定接口。
3. `404` 表示没有找到路由或资源；`422` 表示找到了路由，但提交的数据不合格。
4. 类型标注不仅给人看，FastAPI 和 Pydantic 会利用它生成校验规则和 Swagger 文档。
5. 测试使用的 `http://test` 不是真实网站，只是测试客户端要求提供的基础地址。

## 12. 复盘题

请先不用看代码，用自己的话回答：

1. 路径参数、查询参数和请求正文分别适合什么场景？
路径参数适合表示“具体是哪一个资源”，查询参数适合搜索、筛选、排序和分页，请求正文适合提交结构化数据。

2. 为什么创建自选股列表返回 `201`，而不是 `200`？
201表示创建成功，200表示查询成功。

3. 空名称为什么没有进入 `create_watchlist()` 函数？
因为 Pydantic 在接口函数执行前发现空名称不符合 min_length=1 的规则，所以阻止请求继续进入函数，并由 FastAPI 返回 422。

4. Pydantic 和数据库分别负责什么？
pydantic负责校验数据，数据库负责保存数据。

5. 为什么已经在 Swagger 中验证过，还要保留自动测试？
自动重复执行、回归测试、修改代码后仍能检查

6. `ASGITransport` 为什么不需要启动真实浏览器？
ASGITransport 直接把请求交给内存中的 FastAPI 应用。

7. TDD 中为什么必须先看到测试按预期失败？
证明测试能够发现功能不存在，避免测试本身无效。

## 13. 我的 Day 2 学习记录

请用自己的话填写，不要直接复制上面的讲义。

### 我今天完成了什么？
今天完成了创建自选股列表的接口，并编写了对应的测试。

### 我现在能解释的三个概念

1.路径参数、查询参数和请求正文的区别:路径参数表示具体是哪一个资源，查询参数适合搜索、筛选、排序和分页，请求正文适合提交结构化数据。

2.Pydantic 如何在接口执行前校验数据:Pydantic 在接口执行前校验数据，如果校验失败，FastAPI 会直接返回422，接口函数不会执行。

3.TDD 的 RED → GREEN → 回归测试流程:先写测试，测试失败，编写代码使测试通过，再运行全部测试，确保新功能没有破坏旧功能。

### 我遇到的错误及原因
可以写第一次测试得到 404，原因是路由尚未实现；以及最初把 422 当成原因，后来理解到它其实是校验失败后的结果。

### 我还不理解的内容
“还不能完全脱离讲义解释 Pydantic 的校验流程”

### 明天开始前要复习什么？
HTTP 方法与路径、三种参数、200/201/404/422、TDD 流程
