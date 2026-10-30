-- BBR 2.0a: 0x41F66B writes 0 instead of 140 to the transformed picture offset.
-- Static comparison with pinned original LF2 v2.0a; input EXE was not executed.
return function(base)
    base.record_transform_picture_offset = 0
    return base
end
