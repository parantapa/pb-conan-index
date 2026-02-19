#!/bin/bash

. "$HOME/default-env.sh"

run_clean () {
    # conan remove "random123" --confirm
    # conan remove "gurobi" --confirm
    # conan remove "ortools" --confirm

    # conan remove "munge" --confirm
    # conan remove "openpmix" --confirm
    # conan remove "prrte" --confirm

    # conan remove "rdma-core" --confirm

    # conan remove "openucx" --confirm
    # conan remove "openucc" --confirm
    # conan remove "openmpi" --confirm
}

run_install () {
    # conan create recipes/munge/all/ --version="0.5.17.pci" -vverbose --build=missing
    # conan create recipes/openpmix/all/ --version="5.0.9.pci" -vverbose --build=missing
    # conan create recipes/prrte/all/ --version="3.0.12.pci" -vverbose --build=missing

    # conan create recipes/openucx/all/ --version="1.20.0.pci" -vverbose --build=missing \
    #     --options="openucx/*:cuda=True" \
    #     --options="openucx/*:rdma=True"
    #
    # conan create recipes/openucc/all/ --version="1.6.0.pci" -vverbose --build=missing \
    #     --options="openucx/*:cuda=True" \
    #     --options="openucx/*:rdma=True"

    # conan create -vverbose recipes/openmpi/all/ --version="5.0.9.pci" --options="openmpi/*:cuda=True" --build=missing
    # conan create -vverbose recipes/ortools/all/ --version="9.15.pci" --build=missing
}

show_help() {
    echo "Usage: $0 (help | command)"
}

if [[ "$1" == "help" || "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
elif [[ $(type -t "run_${1}") == function ]]; then
    run_${1}
else
    echo "Unknown command: $1"
fi
