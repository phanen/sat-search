import asyncio
import os

DEP_PATH = "./deps/"

manifestes = {
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


asyncio.run(build_deps(manifestes))
