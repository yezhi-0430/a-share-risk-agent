# 第 2 天学习笔记：FastAPI 请求如何进入业务代码

## 1. 三种输入位置

### 查询参数

```http
GET /api/v1/stocks?query=600519
```

`query` 位于 `?` 后，用于筛选和搜索。对应代码：

```python
async def search_stocks(query: str = Query(min_length=1, max_length=40)):
    ...
```

### 路径参数

```http
DELETE /api/v1/watchlists/1
```

`1` 位于 URL 路径中，对应 `watchlist_id`：

```python
async def delete_watchlist(watchlist_id: int):
    ...
```

FastAPI 会尝试把文本 `1` 转成整数。传入 `/abc` 时，函数执行前就会返回 `422`。

### 请求体

```http
POST /api/v1/watchlists
Content-Type: application/json

{"name": "核心持仓"}
```

JSON 是请求体。FastAPI 将它交给 Pydantic，按 `CreateWatchlistRequest` 校验：

```python
class CreateWatchlistRequest(BaseModel):
    name: WatchlistName
```

## 2. Pydantic 做什么

Pydantic 描述合格数据的形状，并执行转换与校验。本项目规定分组名称去除首尾空格后必须包含 1–40 个字符，股票代码必须符合：

```text
六位数字.SH
六位数字.SZ
六位数字.BJ
```

例如 `600519.SH` 合格，`MOUTAI` 不合格。输入不合格时 FastAPI 返回 `422`，路由函数不会执行。

Pydantic 不负责永久保存数据。当前保存工作由 `MemoryWatchlistRepository` 完成，第 3 天将替换为数据库仓库。

## 3. 一次创建请求的完整流程

```text
POST /api/v1/watchlists
        |
        v
FastAPI 根据方法和路径找到 create_watchlist
        |
        v
Pydantic 校验 JSON 并创建 CreateWatchlistRequest
        |
        v
路由调用 repository.create(payload.name)
        |
        v
仓库检查重名并保存 Watchlist
        |
        v
FastAPI 按 Watchlist 响应模型生成 JSON，返回 201
```

## 4. 为什么分路由和仓库

- 路由理解 HTTP：路径、请求体、`201`、`404`、`409`。
- 仓库理解数据：创建、查询、重命名、删除和重复检查。

如果把两者写在一个函数里，第 3 天接数据库时所有接口都要重写。现在只需用数据库仓库替换内存仓库，API 行为和测试可以保持不变。

## 5. 状态码

- `200 OK`：查询或修改成功。
- `201 Created`：成功创建分组或分组成员。
- `204 No Content`：删除成功，不需要响应体。
- `404 Not Found`：股票或分组不存在。
- `409 Conflict`：分组重名或重复添加股票。
- `422 Unprocessable Content`：输入格式不符合 Pydantic 规则。

## 6. 今天需要能独立回答

1. `GET /stocks?query=平安` 中的 `query` 为什么是查询参数？
2. `/{watchlist_id}` 中的编号为什么是路径参数？
3. Pydantic 和数据库有什么区别？
4. 为什么重复添加股票返回 `409` 而不是 `500`？
5. 如果明天换成 PostgreSQL，哪一层应被替换？

