# Примеры тестов

Справочник к `test-driven-development`: образцы, на которых держатся требования
RED, GREEN, DAMP и запрет горизонтального разреза.

## RED: хороший и плохой тест

**Хороший тест:**
```python
def test_retries_failed_operations_3_times():
    attempts = 0
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception('fail')
        return 'success'

    result = retry_operation(operation)

    assert result == 'success'
    assert attempts == 3
```
Чёткое имя, проверяет реальное поведение, одну вещь.

**Плохой тест:**
```python
def test_retry_works():
    mock = MagicMock()
    mock.side_effect = [Exception(), Exception(), 'success']
    result = retry_operation(mock)
    assert result == 'success'  # What about retry count? Timing?
```
Расплывчатое имя, проверяет заглушку, а не настоящий код.

## GREEN: ровно столько, сколько нужно

**Хорошо:**
```python
def add(a, b):
    return a + b  # Nothing extra
```

**Плохо:**
```python
def add(a, b):
    result = a + b
    logging.info(f"Adding {a} + {b} = {result}")  # Extra!
    return result
```

## DAMP: тест читается как фраза спецификации

```python
def test_rejects_empty_title():
    task = create_task(title="", assignee="user-1")
    ...
```

## Горизонтальный разрез: WRONG и RIGHT

```text
WRONG:
  RED:   test1, test2, test3, test4
  GREEN: impl1, impl2, impl3, impl4

RIGHT:
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
```
