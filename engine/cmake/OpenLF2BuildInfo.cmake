find_package(Git QUIET)
set(openlf2_git_hash "unknown")
if(GIT_FOUND)
    execute_process(COMMAND "${GIT_EXECUTABLE}" rev-parse --short=7 HEAD
        WORKING_DIRECTORY "${OPENLF2_SOURCE_DIR}"
        OUTPUT_VARIABLE openlf2_git_output
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE openlf2_git_result
        ERROR_QUIET)
    if(openlf2_git_result EQUAL 0)
        set(openlf2_git_hash "${openlf2_git_output}")
    endif()
endif()
# Deterministic native-code identity, independent of checkout path and CRLF settings.
file(GLOB_RECURSE openlf2_native_files LIST_DIRECTORIES false
    "${OPENLF2_SOURCE_DIR}/src/*.cpp" "${OPENLF2_SOURCE_DIR}/src/*.mm"
    "${OPENLF2_SOURCE_DIR}/src/*.hpp" "${OPENLF2_SOURCE_DIR}/include/*.hpp")
list(SORT openlf2_native_files)
set(openlf2_native_identity "")
foreach(openlf2_native_file IN LISTS openlf2_native_files)
    file(RELATIVE_PATH openlf2_native_relative "${OPENLF2_SOURCE_DIR}" "${openlf2_native_file}")
    file(READ "${openlf2_native_file}" openlf2_native_text)
    string(REPLACE "\r\n" "\n" openlf2_native_text "${openlf2_native_text}")
    string(SHA256 openlf2_native_digest "${openlf2_native_text}")
    string(APPEND openlf2_native_identity "${openlf2_native_relative}:${openlf2_native_digest}\n")
endforeach()
string(SHA256 openlf2_native_signature "${openlf2_native_identity}")
file(CONFIGURE OUTPUT "${OPENLF2_BUILD_INFO}" CONTENT
    "#pragma once\n#define OPENLF2_BUILD_LABEL \"OpenLF2 ${OPENLF2_VERSION} (${openlf2_git_hash})\"\n#define OPENLF2_ENGINE_SIGNATURE \"${openlf2_native_signature}\"\n")
