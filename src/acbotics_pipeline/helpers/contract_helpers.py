import icontract
from typing import Union, Tuple, Type


from typing import Any, Container
import icontract
from typing import Union, Tuple, Type

desc = ""


def argtype(name: str, types: Union[Type, Tuple[Type, ...]]):
    # Ensure None in a tuple is treated as type(None)
    if isinstance(types, tuple) and None in types:
        types = tuple(t if t is not None else type(None) for t in types)
    elif types is None:
        types = type(None)
    code = (
        f"func = lambda {name}: isinstance({name}, types)\n"
        f"error_func = lambda {name}: icontract.ViolationError(f'{{desc}} (Got: {{{name}}})')"
    )

    ns = {
        "types": types,
        "isinstance": isinstance,
        "icontract": icontract,
        "desc": desc,
    }
    exec(code, ns)
    return icontract.require(
        ns["func"],
        description=f"'{name}' must be {types}",
        error=ns["error_func"],
    )


def argin(name: str, collection: Container):
    ns = {"collection": collection}
    exec(f"func = lambda {name}: {name} in collection", ns)
    return icontract.require(
        ns["func"],
        description=f"'{name}' must be one of {collection}",
        error=lambda **kwargs: icontract.ViolationError(desc),
    )


def arg_positive(name: str):
    desc = f"'{name}' must be > 0"
    ns = {"icontract": icontract, "desc": desc}
    code = (
        f"func = lambda {name}: {name} is not None and {name} > 0\n"
        f"error_func = lambda {name}: icontract.ViolationError(f'{{desc}} (Got: {{{name}}})')"
    )
    exec(code, ns)
    return icontract.require(
        ns["func"],
        description=desc,
        error=ns["error_func"],
    )


def arg_nonnegative(name: str):
    desc = f"'{name}' must be >= 0"
    ns = {"icontract": icontract, "desc": desc}
    code = (
        f"func = lambda {name}: {name} is not None and {name} >= 0\n"
        f"error_func = lambda {name}: icontract.ViolationError(f'{{desc}} (Got:')"
    )
    # {{{name}}})')"    )
    print(code)

    exec(code, ns)
    return icontract.require(
        ns["func"],
        description=desc,
        error=ns["error_func"],
    )


def arg_between(name: str, min_val: float, max_val: float):
    ns = {"min_v": min_val, "max_v": max_val, "icontract": icontract, "desc": desc}

    exec(f"func = lambda {name}: {name} is not None and min_v <= {name} <= max_v", ns)
    return icontract.require(
        ns["func"],
        description=f"'{name}' must be in [{min_val}, {max_val}]",
        error=lambda **kwargs: icontract.ViolationError(desc),
    )


def arg_at_least_one_not_none(*names: str):
    print(names)
    signature = ", ".join([f"{name}=None" for name in names])
    condition = " or ".join([f"{name} is not None" for name in names])
    ns = {}
    # We add **_ to the signature so the lambda accepts 'cls' or 'self'
    # if it's passed, without needing to name them.
    exec(f"func = lambda {signature}, **_: {condition}", ns)
    return icontract.require(
        ns["func"],
        description=f"At least one of {names} must be provided",
        error=lambda **kwargs: icontract.ViolationError(desc),
    )


def member_in_class_var(name: str, class_var_name: str):
    """Checks self.<name> against self.<class_var_name>."""
    return icontract.invariant(
        lambda self: getattr(self, name) in getattr(self, class_var_name),
        description=f"Attribute '{name}' must be valid according to class variable",
        error=lambda **kwargs: icontract.ViolationError(desc),
    )


def member_between(name: str, min_val: Any, max_val: Any):
    """
    Class decorator ensuring min_val <= self.<name> <= max_val.
    """
    return icontract.invariant(
        lambda self: min_val <= getattr(self, name) <= max_val,
        description=f"Attribute '{name}' must be between {min_val} and {max_val}",
        error=lambda **kwargs: icontract.ViolationError(desc),
    )


def member_positive(name: str):
    """Ensures self.<name> is always > 0."""
    return icontract.invariant(
        lambda self: getattr(self, name) > 0,
        description=f"Attribute '{name}' must be strictly positive (> 0)",
        error=lambda **kwargs: icontract.ViolationError(desc),
    )


def member_nonnegative(name: str):
    """Ensures self.<name> is always >= 0."""
    return icontract.invariant(
        lambda self: getattr(self, name) >= 0,
        description=f"Attribute '{name}' must be non-negative (>= 0)",
        error=lambda **kwargs: icontract.ViolationError(desc),
    )


def result_type(types: Union[Type, Tuple[Type, ...]]):
    """Postcondition: Return value must be of a specific type."""
    if isinstance(types, tuple) and None in types:
        types = tuple(t if t is not None else type(None) for t in types)
    elif types is None:
        types = type(None)
    desc = f"Return value must be {types}."

    return icontract.ensure(
        lambda result: isinstance(result, types),
        description=desc,
        # error=BaseException(),
        error=lambda result: icontract.ViolationError(
            f"{desc}. (Got: {type(result).__name__})"
        ),
    )


def result_in(collection: Container):
    """Postcondition: Return value must be in the collection."""
    desc = f"Return value must be in {collection}"
    return icontract.ensure(
        lambda result: result in collection,
        description=desc,
        error=lambda result: icontract.ViolationError(f"{desc}. (Got: {result})"),
    )


def result_between(min_val: Any, max_val: Any):
    """Postcondition: Return value must be between min_val and max_val."""
    desc = f"Return value must be in [{min_val}, {max_val}]"
    return icontract.ensure(
        lambda result: result is not None and min_val <= result <= max_val,
        description=desc,
        error=lambda result: icontract.ViolationError(f"{desc}. (Got: {result})"),
    )


def result_positive():
    """Postcondition: Return value must be > 0."""
    desc = "Return value must be > 0"
    return icontract.ensure(
        lambda result: result is not None and result > 0,
        description=desc,
        error=lambda result: icontract.ViolationError(f"{desc}. (Got: {result})"),
    )


def result_nonnegative():
    """Postcondition: Return value must be >= 0."""
    desc = "Return value must be >= 0"
    return icontract.ensure(
        lambda result: result is not None and result >= 0,
        description=desc,
        error=lambda result: icontract.ViolationError(f"{desc}. (Got: {result})"),
    )
