# Python 基础面试题

## 1. 可变对象与不可变对象

**Python 中的不可变对象：** int、float、str、tuple、frozenset、bytes
**可变对象：** list、dict、set、bytearray

```python
# 不可变：修改会创建新对象
a = 1
b = a
a = 2  # a 指向新对象，b 不变

# 可变：修改原地操作
x = [1, 2, 3]
y = x
x.append(4)  # x 和 y 都变成 [1,2,3,4]
```

## 2. 深拷贝 vs 浅拷贝

- **浅拷贝**：只拷贝外层对象，内层引用不变
- **深拷贝**：递归拷贝所有层级的对象

```python
import copy
original = [[1, 2], [3, 4]]
shallow = copy.copy(original)      # 内层 list 仍引用同一对象
deep = copy.deepcopy(original)     # 完全独立
```

## 3. 装饰器

装饰器本质是**高阶函数**，接收函数作为参数并返回增强后的函数：

```python
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time()-start:.2f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
```

## 4. 生成器与迭代器

- **迭代器**：实现了 `__iter__()` 和 `__next__()` 的对象
- **生成器**：用 `yield` 关键字创建，是迭代器的简化写法
- **优势**：惰性求值，节省内存

## 5. GIL 与多线程

GIL（全局解释器锁）：
- CPython 的实现限制，同一时刻只有一个线程执行
- **IO 密集型**：多线程有效（等待 IO 时释放 GIL）
- **CPU 密集型**：用多进程 `multiprocessing`
