__all__ = (
    # core (exceptions)
    'ExceptionGroup', 'BaseExceptionGroup', 'InvalidStateError', 'Cancelled',

    # core
    'Aw_or_Task', 'start', 'Task', 'TaskState',
    'dummy_task', 'current_task', '_current_task', 'sleep_forever', '_sleep_forever',

    # structured concurrency
    'wait_all', 'wait_any', 'wait_all_cm', 'wait_any_cm', 'move_on_when',
    'run_as_main', 'run_as_daemon',
    'open_nursery', 'Nursery',

    # synchronization
    'Event', 'ExclusiveEvent', 'StatefulEvent', 'StatelessEvent',
)
import types
import typing as T
from inspect import getcoroutinestate, CORO_CREATED, CORO_SUSPENDED, isawaitable
import sys
import itertools
from functools import cached_property, partial
import enum
from contextlib import asynccontextmanager, contextmanager

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------

if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup, ExceptionGroup
else:
    BaseExceptionGroup = BaseExceptionGroup  #: :meta private:
    ExceptionGroup = ExceptionGroup  #: :meta private:

potential_bug_msg = \
    r"You might found a bug in the library. Please make a minimal code that reproduces it, " \
    r"and open an issue at the GitHub repository, then post the code there. (https://github.com/asyncgui/asyncgui)."


class InvalidStateError(Exception):
    """Operation is not allowed in the current state."""


class _Cancelled(BaseException):
    @cached_property
    def level(self) -> int:
        return self.args[0]


Cancelled = (_Cancelled, GeneratorExit, )
'''
Exception class that represents cancellation.
See :ref:`dealing-with-cancellation`.

.. warning::

    Actually, this is not an exception class but a tuple of exception classes for now.
    But that's an implementation detail, and it might become an actual class in the future;
    therefore, your code must be compatible in both cases.

:meta hide-value:
'''


class TaskState(enum.Enum):
    '''
    Enum class that represents the Task state.
    '''

    CREATED = enum.auto()
    '''
    Waiting to start execution.

    :meta hide-value:
    '''

    STARTED = enum.auto()
    '''
    Currently running or suspended.

    :meta hide-value:
    '''

    CANCELLED = enum.auto()
    '''
    The execution has been cancelled. The cause of the cancellation is either an explicit or implicit call to
    :meth:`Task.cancel` or an unhandled exception.

    :meta hide-value:
    '''

    FINISHED = enum.auto()
    '''
    The execution has been completed.

    :meta hide-value:
    '''


_next_Task_uid = itertools.count().__next__


class Task:
    __slots__ = (
        '_uid', '_root_coro', '_root_coro_send', '_state', '_result', '_on_end',
        '_exc_caught', '_suppresses_exc',
        '_cancel_disabled', '_current_depth', '_requested_cancel_level',
    )

    def __init__(self, aw: T.Awaitable, /):
        if not isawaitable(aw):
            raise ValueError(str(aw) + " is not awaitable.")
        self._uid = _next_Task_uid()
        self._cancel_disabled = False
        self._root_coro = self._wrapper(aw)
        self._root_coro_send = self._root_coro.send
        self._state = TaskState.CREATED
        self._on_end = None
        self._current_depth = 0
        self._requested_cancel_level = None
        self._exc_caught = None
        self._suppresses_exc = False

    def __str__(self):
        return f'Task(state={self._state.name}, uid={self._uid})'

    @property
    def uid(self) -> int:
        '''
        An unique integer assigned to the task.
        '''
        return self._uid

    @property
    def root_coro(self) -> T.Coroutine:
        '''
        The starting point of the coroutine chain for the task.
        '''
        return self._root_coro

    @property
    def state(self) -> TaskState:
        '''
        The current state of the task.
        '''
        return self._state

    @property
    def finished(self) -> bool:
        '''Whether the task has completed execution.'''
        return self._state is TaskState.FINISHED

    @property
    def cancelled(self) -> bool:
        '''Whether the task has been cancelled.'''
        return self._state is TaskState.CANCELLED

    @property
    def result(self) -> T.Any:
        '''Result of the task. If the task is not finished, :exc:`InvalidStateError` will be raised. '''
        state = self._state
        if state is TaskState.FINISHED:
            return self._result
        elif state is TaskState.CANCELLED:
            raise InvalidStateError(f"{self} was cancelled")
        else:
            raise InvalidStateError(f"Result of {self} is not ready")

    async def _wrapper(self, aw, /):
        try:
            self._state = TaskState.STARTED
            self._result = await aw
        except _Cancelled as e:
            self._state = TaskState.CANCELLED
            assert e.level == 0, potential_bug_msg
            assert self._requested_cancel_level == 0, potential_bug_msg
        except Exception as e:
            self._state = TaskState.CANCELLED
            self._exc_caught = e
            if not self._suppresses_exc:
                raise
        except:  # noqa: E722
            self._state = TaskState.CANCELLED
            raise
        else:
            self._state = TaskState.FINISHED
        finally:
            assert self._current_depth == 0, potential_bug_msg
            if (on_end := self._on_end) is not None:
                on_end(self)

    def cancel(self, _level=0, /):
        '''Cancel the task as soon as possible.'''
        if self._requested_cancel_level is None:
            self._requested_cancel_level = _level
            state = getcoroutinestate(self._root_coro)
            if state is CORO_SUSPENDED:
                if not self._cancel_disabled:
                    self._actual_cancel()
            elif state is CORO_CREATED:
                self._root_coro.close()
                self._state = TaskState.CANCELLED
        else:
            self._requested_cancel_level = min(self._requested_cancel_level, _level)

    def _actual_cancel(self):
        try:
            self._root_coro.throw(_Cancelled(self._requested_cancel_level))(self)
        except StopIteration:
            pass
        else:
            self._cancel_if_needed()

    close = cancel
    '''An alias of :meth:`cancel`.'''

    @property
    def _cancel_requested(self) -> bool:
        return self._requested_cancel_level is not None

    @property
    def _is_cancellable(self, get_state=getcoroutinestate, CORO_SUSPENDED=CORO_SUSPENDED) -> bool:
        '''Whether the task can be cancelled immediately.'''
        return (not self._cancel_disabled) and get_state(self._root_coro) is CORO_SUSPENDED

    def _cancel_if_needed(self):
        if (self._requested_cancel_level is not None) and self._is_cancellable:
            self._actual_cancel()

    def _step(self, *args, **kwargs):
        try:
            self._root_coro_send((args, kwargs, ))(self)
        except StopIteration:
            pass
        else:
            self._cancel_if_needed()

    def _throw_exc(self, exc):
        '''停止中のTaskへ例外を投げる。Taskが停止中ではない場合は :exc:`InvalidStateError` が起こる。'''
        coro = self._root_coro
        if getcoroutinestate(coro) is not CORO_SUSPENDED:
            raise InvalidStateError("Throwing an exception to an unstarted/running/closed task is not allowed.")
        try:
            coro.throw(exc)(self)
        except StopIteration:
            pass
        else:
            self._cancel_if_needed()

    class CancelScope:
        __slots__ = ('_task', '_depth', 'cancel_called', )

        def __init__(self, task, depth):
            self._task = task
            self._depth = depth
            self.cancel_called = False

        @property
        def closed(self) -> bool:
            return self._task is None

        def cancel(self):
            if self.cancel_called:
                return
            self.cancel_called = True
            if (t := self._task) is not None:
                t.cancel(self._depth)

    @contextmanager
    def _open_cancel_scope(self, CancelScope=CancelScope):
        self._current_depth = depth = self._current_depth + 1
        scope = CancelScope(self, depth)
        try:
            yield scope
        except _Cancelled as exc:
            level = exc.level
            if level != depth:
                assert level < depth, potential_bug_msg
                raise
        finally:
            req_level = self._requested_cancel_level
            scope._task = None
            self._current_depth -= 1
            if req_level is not None:
                if req_level == depth:
                    self._requested_cancel_level = None
                else:
                    assert req_level < depth, potential_bug_msg

    del CancelScope


Aw_or_Task = T.Union[T.Awaitable, Task]


def start(aw: Aw_or_Task, /) -> Task:
    '''*Immediately* start a Task/Awaitable.

    If the argument is a :class:`Task`, itself will be returned. If it's an :class:`typing.Awaitable`,
    it will be wrapped in a Task, and that Task will be returned.

    .. code-block::

        async def async_func():
            ...

        task = start(async_func())
    '''
    if isawaitable(aw):
        task = Task(aw)
    elif isinstance(aw, Task):
        task = aw
        if task._state is not TaskState.CREATED:
            raise ValueError(f"{task} has already started")
    else:
        raise ValueError("Argument must be either a Task or an awaitable.")

    try:
        task._root_coro_send(None)(task)
    except StopIteration:
        pass
    else:
        task._cancel_if_needed()

    return task


def _current_task(task):
    return task._step(task)


@types.coroutine
def current_task(_f=_current_task) -> T.Awaitable[Task]:
    '''Returns the Task instance corresponding to the caller.

    .. code-block::

        task = await current_task()
    '''
    return (yield _f)[0][0]


def _sleep_forever(task):
    pass


@types.coroutine
def sleep_forever(_f=_sleep_forever) -> T.Awaitable:
    '''
    .. code-block::

        await sleep_forever()
    '''
    yield _f


dummy_task = Task(sleep_forever())
'''
An already closed task.
This can be utilized to prevent the need for the common null validation mentioned below.

*Before:*

.. code-block::
    :emphasize-lines: 3, 6,7

    class MyClass:
        def __init__(self):
            self._task = None

        def restart(self):
            if self._task is not None:
                self._task.cancel()
            self._task = asyncgui.start(self.main())

        async def main(self):
            ...

*After:*

.. code-block::
    :emphasize-lines: 3, 6

    class MyClass:
        def __init__(self):
            self._task = asyncgui.dummy_task

        def restart(self):
            self._task.cancel()
            self._task = asyncgui.start(self.main())

        async def main(self):
            ...
'''
dummy_task.cancel()

# -----------------------------------------------------------------------------
# Synchronization
# -----------------------------------------------------------------------------


class ExclusiveEvent:
    '''
    Similar to :class:`Event`, but this version does not allow multiple tasks to :meth:`wait` simultaneously.
    As a result, it operates faster.
    '''
    __slots__ = ('_callback', )

    def __init__(self):
        self._callback = None

    def fire(self, *args, **kwargs):
        if (f := self._callback) is not None:
            f(*args, **kwargs)

    @types.coroutine
    def wait(self) -> T.Awaitable[tuple]:
        if self._callback is not None:
            raise InvalidStateError("There's already a task waiting for the event to fire.")
        try:
            return (yield self._attach_task)
        finally:
            self._callback = None

    def _attach_task(self, task):
        self._callback = task._step


class Event:
    '''
    .. code-block::

        async def async_fn(e):
            args, kwargs = await e.wait()
            assert args == (2, )
            assert kwargs == {'crow': 'raven', }

            args, kwargs = await e.wait()
            assert args == (3, )
            assert kwargs == {'toad': 'frog', }

        e = Event()
        e.fire(1, crocodile='alligator')
        task = start(async_fn(e))
        e.fire(2, crow='raven')
        e.fire(3, toad='frog')
        assert task.finished

    .. warning::

        This differs significantly from :class:`asyncio.Event`, as this one does not have a "set" state.
        When a Task calls its :meth:`wait` method, it will always be blocked until :meth:`fire` is called *after* that.
        Use :class:`StatefulEvent` if you want something closer to :class:`asyncio.Event`.

    .. versionchanged:: 0.7.0

        This is now completely different from the previous version's.
    '''

    __slots__ = ('_waiting_tasks', )

    def __init__(self):
        self._waiting_tasks = []

    def fire(self, *args, **kwargs):
        tasks = self._waiting_tasks
        self._waiting_tasks = []
        for t in tasks:
            if t is not None:
                t._step(*args, **kwargs)

    @types.coroutine
    def wait(self) -> T.Awaitable[tuple]:
        '''
        Waits for the event to be fired.
        '''
        try:
            tasks = self._waiting_tasks
            idx = len(tasks)
            return (yield tasks.append)
        finally:
            tasks[idx] = None


StatelessEvent = Event
'''
An alias of :class:`Event`.

.. versionadded:: 0.7.2
'''


class StatefulEvent:
    '''
    The closest thing to :class:`asyncio.Event` in this library.

    .. csv-table::
        :header-rows: 1

        StatefulEvent, asyncio.Event
        .fire(), .set()
        .wait(), .wait()
        .clear(), .clear()
        .is_fired, .is_set()
        .params, --

    .. code-block::

        async def async_fn(e):
            args, kwargs = await e.wait()
            assert args == (1, )
            assert kwargs == {'crow': 'raven', }

        e = StatefulEvent()
        task = start(async_fn(e))
        assert not task.finished
        e.fire(1, crow='raven')
        assert task.finished

    .. versionadded:: 0.7.2

    .. versionchanged:: 0.9.0
        The ``.refire()`` and ``.fire_or_refire()`` methods have been removed.
    '''
    __slots__ = ('_params', '_waiting_tasks', )

    def __init__(self):
        self._params = None
        self._waiting_tasks = []

    @property
    def is_fired(self) -> bool:
        return self._params is not None

    def fire(self, *args, **kwargs):
        '''Fires the event if it's not in a fired state.'''
        if self._params is not None:
            return
        self._params = (args, kwargs, )
        tasks = self._waiting_tasks
        self._waiting_tasks = []
        for t in tasks:
            if t is not None:
                t._step(*args, **kwargs)

    def clear(self):
        '''Sets the event to a non-fired state.'''
        self._params = None

    @types.coroutine
    def wait(self) -> T.Awaitable[tuple]:
        if self._params is not None:
            return self._params
        tasks = self._waiting_tasks
        idx = len(tasks)
        try:
            return (yield tasks.append)
        finally:
            tasks[idx] = None

    @property
    def params(self) -> tuple:
        '''
        The parameters passed to the last fire. Raises :exc:`InvalidStateError` if the event is not in a "fired" state.
        This is a convenient way to access the parameters from synchronous code.

        .. code-block::

            e = StatefulEvent()

            e.fire(1, crow='raven')
            args, kwargs = e.params
            assert args == (1, )
            assert kwargs == {'crow': 'raven', }

            e.clear()
            e.fire(2, parasol='umbrella')
            args, kwargs = e.params
            assert args == (2, )
            assert kwargs == {'parasol': 'umbrella', }
        '''
        p = self._params
        if p is None:
            raise InvalidStateError("The event is not in a 'fired' state.")
        return p


# -----------------------------------------------------------------------------
# Structured concurrency
# -----------------------------------------------------------------------------


class TaskCounter:
    '''
    (internal)
    数値が零になった事を通知する仕組みを持つカウンター。
    親taskが自分の子task達の終了を待つのに用いる。
    '''

    __slots__ = ('_parent', '_n_children', )

    def __init__(self, initial=0, /):
        self._n_children = initial
        self._parent = None

    def increase(self):
        self._n_children += 1

    def decrease(self, potential_bug_msg=potential_bug_msg):
        n = self._n_children - 1
        assert n >= 0, potential_bug_msg
        self._n_children = n
        if (parent := self._parent) is not None and (not n):
            parent._step()

    @types.coroutine
    def to_be_zero(self, _current_task=_current_task, _sleep_forever=_sleep_forever):
        if not self._n_children:
            return
        self._parent = (yield _current_task)[0][0]
        try:
            yield _sleep_forever
        finally:
            self._parent = None

    def __bool__(self):
        return not not self._n_children  # 'not not' is not a typo


async def _wait_xxx(debug_msg, on_child_end, *aws: T.Iterable[Aw_or_Task]) -> T.Awaitable[T.Sequence[Task]]:
    children = tuple(v if isinstance(v, Task) else Task(v) for v in aws)
    if not children:
        return children
    counter = TaskCounter(len(children))
    parent = await current_task()

    try:
        with parent._open_cancel_scope() as scope:
            on_child_end = partial(on_child_end, scope, counter)
            for c in children:
                c._suppresses_exc = True
                c._on_end = on_child_end
                start(c)
            await counter.to_be_zero()
    finally:
        if counter:
            for c in children:
                c.cancel()
            if counter:
                try:
                    parent._cancel_disabled = True
                    await counter.to_be_zero()
                finally:
                    parent._cancel_disabled = False
        exceptions = tuple(e for c in children if (e := c._exc_caught) is not None)
        if exceptions:
            raise ExceptionGroup(debug_msg, exceptions)
        if (parent._requested_cancel_level is not None) and (not parent._cancel_disabled):
            await sleep_forever()
            assert False, potential_bug_msg
    return children


def _on_child_end__ver_all(scope, counter, child):
    counter.decrease()
    if child._exc_caught is not None:
        scope.cancel()


def _on_child_end__ver_any(scope, counter, child):
    counter.decrease()
    if child._exc_caught is not None or child.finished:
        scope.cancel()


_wait_xxx_type = T.Callable[..., T.Awaitable[T.Sequence[Task]]]
wait_all: _wait_xxx_type = partial(_wait_xxx, "wait_all()", _on_child_end__ver_all)
'''
Run multiple tasks concurrently, and wait for **all** of them to **end**. When any of them raises an exception, the
others will be cancelled, and the exception will be propagated to the caller, like :class:`trio.Nursery`.

.. code-block::

    tasks = await wait_all(async_fn1(), async_fn2(), async_fn3())
    if tasks[0].finished:
        print("The return value of async_fn1() :", tasks[0].result)
'''
wait_any: _wait_xxx_type = partial(_wait_xxx, "wait_any()", _on_child_end__ver_any)
'''
Run multiple tasks concurrently, and wait for **any** of them to **finish**. As soon as that happens, the others will be
cancelled. When any of them raises an exception, the others will be cancelled, and the exception will be propagated to
the caller, like :class:`trio.Nursery`.

.. code-block::

    tasks = await wait_any(async_fn1(), async_fn2(), async_fn3())
    if tasks[0].finished:
        print("The return value of async_fn1() :", tasks[0].result)
'''


@asynccontextmanager
async def _wait_xxx_cm(debug_msg, on_child_end, wait_bg, aw: Aw_or_Task):
    counter = TaskCounter(1)
    fg_task = await current_task()
    bg_task = aw if isinstance(aw, Task) else Task(aw)
    exc = None

    try:
        with fg_task._open_cancel_scope() as scope:
            bg_task._on_end = partial(on_child_end, scope, counter)
            bg_task._suppresses_exc = True
            yield start(bg_task)
            if wait_bg:
                await counter.to_be_zero()
    except Exception as e:
        exc = e
    finally:
        bg_task.cancel()
        if counter:
            try:
                fg_task._cancel_disabled = True
                await counter.to_be_zero()
            finally:
                fg_task._cancel_disabled = False
        excs = tuple(
            e for e in (exc, bg_task._exc_caught, )
            if e is not None
        )
        if excs:
            raise ExceptionGroup(debug_msg, excs)
        if (fg_task._requested_cancel_level is not None) and (not fg_task._cancel_disabled):
            await sleep_forever()
            assert False, potential_bug_msg


_wait_xxx_cm_type = T.Callable[[Aw_or_Task], T.AsyncContextManager[Task]]
wait_all_cm: _wait_xxx_cm_type = partial(_wait_xxx_cm, "wait_all_cm()", _on_child_end__ver_all, True)
'''
The context manager form of :func:`wait_all`.

.. code-block::

    async with wait_all_cm(async_fn()) as bg_task:
        ...
'''
wait_any_cm: _wait_xxx_cm_type = partial(_wait_xxx_cm, "wait_any_cm()", _on_child_end__ver_any, False)
'''
The context manager form of :func:`wait_any`, an equivalence of :func:`trio_util.move_on_when`.

.. code-block::

    async with wait_any_cm(async_fn()) as bg_task:
        ...
'''
run_as_main: _wait_xxx_cm_type = partial(_wait_xxx_cm, "run_as_main()", _on_child_end__ver_any, True)
'''
.. code-block::

    async with run_as_main(async_fn()) as task:
        ...
'''
run_as_daemon: _wait_xxx_cm_type = partial(_wait_xxx_cm, "run_as_daemon()", _on_child_end__ver_all, False)
'''
.. code-block::

    async with run_as_daemon(async_fn()) as bg_task:
        ...
'''


class Nursery:
    '''
    Similar to :class:`trio.Nursery`.
    You should not directly instantiate this, use :func:`open_nursery`.
    '''

    __slots__ = ('_closed', '_children', '_scope', '_counters', '_callbacks', '_gc_in_every', '_n_until_gc', )

    def __init__(self, scope, counter, daemon_counter, gc_in_every):
        self._gc_in_every = self._n_until_gc = gc_in_every
        self._closed = False
        self._children = []
        self._scope = scope
        self._counters = (daemon_counter, counter, )
        self._callbacks = (
            partial(_on_child_end__ver_all, scope, daemon_counter),
            partial(_on_child_end__ver_all, scope, counter),
        )

    def start(self, aw: Aw_or_Task, /, *, daemon=False) -> Task:
        '''
        *Immediately* start a Task/Awaitable under the supervision of the nursery.

        If the argument is a :class:`Task`, itself will be returned. If it's an :class:`typing.Awaitable`,
        it will be wrapped in a Task, and that Task will be returned.

        The ``daemon`` parameter acts like the one in the :mod:`threading` module.
        When only daemon tasks are left, they get cancelled, and the nursery closes.
        '''
        if self._closed:
            raise InvalidStateError("Nursery has been already closed")
        if not self._n_until_gc:
            self._collect_garbage()
            self._n_until_gc = self._gc_in_every
        self._n_until_gc -= 1
        child = aw if isinstance(aw, Task) else Task(aw)
        child._suppresses_exc = True
        child._on_end = self._callbacks[not daemon]
        self._counters[not daemon].increase()
        self._children.append(child)
        return start(child)

    def _collect_garbage(self, STARTED=TaskState.STARTED):
        self._children = [
            c for c in self._children
            if c.state is STARTED or c._exc_caught is not None
        ]

    def close(self):
        '''Cancel all the child tasks in the nursery as soon as possible. '''
        self._closed = True
        self._scope.cancel()

    @property
    def closed(self) -> bool:
        return self._closed


@asynccontextmanager
async def open_nursery(*, _gc_in_every=1000) -> T.AsyncContextManager[Nursery]:
    '''
    Similar to :func:`trio.open_nursery`.

    .. code-block::

        async with open_nursery() as nursery:
            nursery.start(async_fn1())
            nursery.start(async_fn2(), daemon=True)
    '''
    exc = None
    parent = await current_task()
    counter = TaskCounter()
    daemon_counter = TaskCounter()

    try:
        with parent._open_cancel_scope() as scope:
            nursery = Nursery(scope, counter, daemon_counter, _gc_in_every)
            yield nursery
            await counter.to_be_zero()
    except Exception as e:
        exc = e
    finally:
        nursery._closed = True
        children = nursery._children
        for c in children:
            c.cancel()
        try:
            parent._cancel_disabled = True
            await daemon_counter.to_be_zero()
            await counter.to_be_zero()
        finally:
            parent._cancel_disabled = False
        excs = tuple(
            e for e in itertools.chain((exc, ), (c._exc_caught for c in children))
            if e is not None
        )
        if excs:
            raise ExceptionGroup("Nursery", excs)
        if (parent._requested_cancel_level is not None) and (not parent._cancel_disabled):
            await sleep_forever()
            assert False, potential_bug_msg


# -----------------------------------------------------------------------------
# Aliases
# -----------------------------------------------------------------------------

move_on_when = wait_any_cm
'''
An alias of :func:`wait_any_cm`, which is equivalent to :func:`trio_util.move_on_when`.
'''
