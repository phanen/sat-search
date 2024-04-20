import asyncio
import os

DEP_PATH = "./deps/"

sources = {
    "cadical": {
        "repo": "https://github.com/arminbiere/cadical",
        "build": "./configure && make",
    },
    "cryptominisat": {
        "repo": "https://github.com/msoos/cryptominisat",
        "build": "cmake -B build && cmake --build build",
    },
    "kissat": {
        "repo": "https://github.com/arminbiere/kissat",
        "build": "cmake -B build && cmake --build build",
    },
    "glucose-syrup": {
        "repo": "https://github.com/audemard/glucose",
        "build": "cmake -Bbuild && cmake --build build",
    },
    "lingeling": {
        "repo": "https://github.com/arminbiere/lingeling",
        "build": "./configure.sh && make",
    },
    "maplesat": {
        "repo": "https://github.com/curtisbright/maplesat",
        "build": "make",
    },
    # "piconsat": {
    #     "repo": "https://github.com/conda/pycosat",
    #     "build": "make PYTHON=python",
    # },
}


# async clone repo then build it
async def clone_and_build(name, repo_url, build_cmd):
    repo_dir = DEP_PATH + name
    if not os.path.exists(repo_dir):
        print(f"Cloning {repo_url} to {repo_dir}...")
        clone_proc = await asyncio.create_subprocess_exec(
            "git", "clone", repo_url, repo_dir
        )
        await clone_proc.wait()

    print(f"Bulding {name}...")
    build_proc = await asyncio.create_subprocess_shell(build_cmd, cwd=repo_dir)
    await build_proc.wait()


async def build_deps(manifestes):
    tasks = []
    for name, info in manifestes.items():
        task = asyncio.create_task(clone_and_build(name, info["repo"], info["build"]))
        tasks.append(task)
    await asyncio.gather(*tasks)


asyncio.run(build_deps(sources))
