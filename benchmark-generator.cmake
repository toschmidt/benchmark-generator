set(BENCHMARK_GENERATOR ${CMAKE_CURRENT_LIST_DIR}/benchmark-generator.py)

function(generate_benchmarks_from_folder folder BENCHMARKS)
    if (${CMAKE_VERSION} VERSION_LESS "3.19")
        message(WARNING "Cannot generate benchmarks CMake 3.19 or higher is required. You are running version ${CMAKE_VERSION}")
        message(WARNING "Using second last filename extension instead (deprecated)")
        return()
    endif ()

    file(GLOB_RECURSE jsons RELATIVE ${folder} *.json)

    foreach (json ${jsons})
        get_filename_component(dir ${json} DIRECTORY)
        get_filename_component(name ${json} NAME_WE)

        if (${CMAKE_VERSION} VERSION_LESS "3.19")
            string(REPLACE "." ";" ext_list ${json})
            list(GET ext_list -2 type)
        else ()
            file(READ ${folder}/${json} json_data)
            string(JSON type GET ${json_data} type)
        endif ()

        if (${type} STREQUAL "definition")
            SET(json_schema ${folder}/${dir}/${name}.schema.json)

            add_custom_command(
                    OUTPUT ${json_schema}
                    COMMAND ${BENCHMARK_GENERATOR} --schema --input ${folder}/${json} --output ${json_schema}
                    DEPENDS ${folder}/${json}
                    VERBATIM)
            # target to generate benchmark schema
            add_custom_target(schema_${name} ALL DEPENDS ${json_schema})

        elseif (${type} STREQUAL "benchmark")
            set(cpp generated/${name}.cpp)

            # ${cpp}.output is never created, therefore, the command is run on every build
            add_custom_command(
                    OUTPUT ${cpp} ${cpp}.output
                    COMMAND ${BENCHMARK_GENERATOR} --benchmark --input ${folder}/${json} --output ${cpp}
                    VERBATIM)
            add_executable(benchmark_${name} ${cpp})
            list(APPEND benchmark_drivers benchmark_${name})
        endif ()

    endforeach ()

    set(${BENCHMARKS} ${benchmark_drivers} PARENT_SCOPE)
endfunction()
