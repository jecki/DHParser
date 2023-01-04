
# template newObj*(T: typedesc, args: varargs[untyped]): untyped =
#   ## requires the init-procedure to return the object passed as first parameter
#   new(T).`init`(args)

# template newObj*(T: typedesc, args: varargs[untyped]): untyped =
#   let obj = new(T)
#   obj.init(args)
#   obj

template newObj*(T: typedesc, args: varargs[untyped]): T =
  new(result)
  result.init(args)