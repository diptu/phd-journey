def run(script):
    import subprocess

    print(f"▶️ Running {script} ...")
    subprocess.check_call(["python3", script])


if __name__ == "__main__":
    print("🚀 Starting Full Academic Intelligence Pipeline")

    run("uni_registry.py")
    run("faculty_registry.py")
    run("research_registry.py")

    print("🏁 Pipeline completed successfully")
