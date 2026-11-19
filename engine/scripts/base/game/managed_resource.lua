-- SPDX-License-Identifier: MIT
-- Resolve converter-generated DAT image references within their own package.
local local_image = "^%./a/%d%d%d%d%d%d%."
local function resolve(dat_path, resource)
    if not resource or not resource:match(local_image) then return resource end
    local namespace = dat_path:match("^(mods/[a-z][a-z0-9-]+/)a/%d%d%d%d%d%d%.dat$")
    if namespace and (resource:match(local_image .. "bmp$") or resource:match(local_image .. "png$")) then
        return namespace .. resource:sub(3)
    end
    return resource
end
return {resolve = resolve}
